# Seed the database with sample data for testing and development.
# Usage: python -m backend.app.scripts.seed

import asyncio
import random
from datetime import datetime, timedelta, timezone

from faker import Faker
from keybert import KeyBERT
from sentence_transformers import SentenceTransformer
from sqlalchemy import func, select
from transformers import pipeline

from backend.app.core.aspects import ASPECTS
from backend.app.core.database import Base, engine
from backend.app.core.ml_registry import MLRegistry
from backend.app.core.security import hash_password
from backend.app.services.absa_service import run_absa_for_review
from backend.app.services.sentiment_service import analyze_sentiment_batch
from backend.app.services.vibe_snapshot_service import create_vibe_snapshot

from ..core.database import AsyncSessionLocal
from ..models.business import Business
from ..models.review import Review
from ..models.user import User

fake = Faker()


# Sample data for review generation
FEATURES = [
    "beachfront resort",
    "mountain resort",
    "island resort",
    "luxury villa",
    "family resort",
]

POSITIVE_ASPECTS = [
    "clean rooms",
    "friendly staff",
    "amazing view",
    "relaxing atmosphere",
    "excellent service",
    "delicious food",
    "well-maintained facilities",
]

NEGATIVE_ASPECTS = [
    "dirty rooms",
    "slow service",
    "poor maintenance",
    "bad food quality",
    "noisy environment",
    "broken amenities",
    "unresponsive staff",
]

BUSINESS_VIBE_PROFILES = {
    "improving": {"base": -0.4, "growth": 0.015},
    "kind_stable": {"base": 0.1, "growth": 0.0},
    "stable": {"base": 0.6, "growth": 0.0},
    "declining": {"base": 0.7, "growth": -0.015},
}

# -----------------------------
# Helper functions for seeding
# -----------------------------


FIXED_PASSWORD = "09232929"

def create_seed_users():
    """
    Creates:
    - 5 business owners
    - 5 regular users
    """
    users = []
    owners = []

    for i in range(5):
        owner = User(
            username=fake.unique.user_name(),
            firstname=fake.first_name(),
            lastname=fake.last_name(),
            role="owner",
            hashed_password=hash_password(FIXED_PASSWORD),
        )
        users.append(owner)
        owners.append(owner)

    for i in range(5):
        user = User(
            username=fake.unique.user_name(),
            firstname=fake.first_name(),
            lastname=fake.last_name(),
            role="user",
            hashed_password=hash_password(FIXED_PASSWORD),
        )
        users.append(user)

    return users, owners

async def get_first_review_date(db, business_id: int):
    """
    Get the date of the first review for a business to determine how far back to backfill vibe snapshots.
    If there are no reviews, return None and skip backfilling.
    """
    result = await db.execute(
        select(Review.created_at).where(
            Review.business_id == business_id
        ).order_by(Review.created_at.asc()).limit(1)
    )
    return result.scalar()


async def backfill_vibe_snapshots(db, business_id: int, models: MLRegistry):
    """
    Backfill vibe snapshots for a business starting from the date of the first review up to today.
    Creates 1 snapshot per day to ensure consistent time-series data for analytics and forecasting.
    """
    first_date = await get_first_review_date(db, business_id)

    if not first_date:
        return

    # Ensure first_date is timezone-aware in UTC for consistent snapshot creation
    if first_date.tzinfo is None:
        first_date = first_date.replace(tzinfo=timezone.utc)
    else:
        first_date = first_date.astimezone(timezone.utc)

    today = datetime.now(timezone.utc)
    current = first_date
    snapshots_created = 0

    # Backfill 1 snapshot per day from first review to today
    # No minimum threshold - create snapshot every single day for consistent time-series data
    while current <= today:
        snapshot = await create_vibe_snapshot(
            db,
            business_id,
            models,
            snapshot_date=current,
            use_ai_summary=False,  # Skip AI summary for backfill to save time - focus on vibe score and label
        )
        if snapshot is not None:
            snapshots_created += 1
        current += timedelta(days=1)
    
    if snapshots_created > 0:
        print(f"  Created {snapshots_created} snapshots for business {business_id}")


def get_sentiment_stage(vibe_type: str, progress: float):
    """
    Determines the sentiment stage (positive, neutral, negative) for a review 
    based on the business's vibe profile and the review's position in the timeline. 
    This allows us to generate reviews that align with the intended vibe trajectory of each business.
    """
    if vibe_type == "improving":
        if progress < 0.4:
            return "negative"
        elif progress < 0.7:
            return "neutral"
        else:
            return "positive"

    elif vibe_type == "declining":
        if progress < 0.4:
            return "positive"
        elif progress < 0.7:
            return "neutral"
        else:
            return "negative"

    elif vibe_type == "stable":
        return "positive"

    elif vibe_type == "kind_stable":
        return "neutral"

def generate_review_from_stage(stage: str):
    feature = random.choice(FEATURES)
    pos = random.choice(POSITIVE_ASPECTS)
    neg = random.choice(NEGATIVE_ASPECTS)

    if stage == "positive":
        return f"The {feature} was excellent. We loved {pos}."

    if stage == "neutral":
        return f"The {feature} was okay. It had {pos}, but also some issues."

    if stage == "negative":
        return f"Very disappointing {feature}. We experienced {neg}."
    

def add_noise(text: str):
    """
    Adds optional noise to review text for realism, such as hedging phrases or filler words. 
    This helps create more natural and varied reviews that better mimic real user-generated content.
    """
    noise = [
        "overall though",
        "still worth mentioning",
        "honestly",
        "to be fair",
        ""
    ]
    return text + " " + random.choice(noise)


def generate_review_by_vibe(vibe_type: str, day_index: int, total: int = 30):

    progress = day_index / total
    stage = get_sentiment_stage(vibe_type, progress)

    base_text = generate_review_from_stage(stage)

    # optional realism layer
    if random.random() < 0.4:
        base_text = add_noise(base_text)

    return base_text

def generate_created_at_with_bias() -> datetime:
    start, end = random.choices([
        ("-6M", "-5M"),
        ("-5M", "-4M"),
        ("-4M", "-3M"),
        ("-3M", "-2M"),
        ("-2M", "-1M"),
        ("-1M", "now"),
    ], weights=[1]*6)[0]

    dt = fake.date_time_between(start_date=start, end_date=end)

    # FORCE UTC
    return dt.replace(tzinfo=timezone.utc)

async def seed() -> None:
    print("Loading ML models...")

    sentiment_model = pipeline(
        "sentiment-analysis",
        model="distilbert-base-uncased-finetuned-sst-2-english"
    )

    embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
    aspect_texts = list(ASPECTS.values())
    aspect_embeddings = embedding_model.encode(aspect_texts, convert_to_tensor=True)
    keyword_extractor_model = KeyBERT(model=embedding_model)

    models = MLRegistry(
        sentiment=sentiment_model,
        embedding=embedding_model,
        aspect_embeddings=aspect_embeddings,
        keyword_extractor=keyword_extractor_model
    )

    async with AsyncSessionLocal() as db:

        # -----------------------------
        # Setup DB
        # -----------------------------
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        await db.execute(Review.__table__.delete())
        await db.execute(Business.__table__.delete())
        await db.execute(User.__table__.delete())
        await db.commit()

        # -----------------------------
        # USERS (5 owners + 5 users)
        # -----------------------------
        print("Seeding users...")

        users = []
        owners = []

        for _ in range(5):
            owner = User(
                username=fake.unique.user_name(),
                firstname=fake.first_name(),
                lastname=fake.last_name(),
                role="owner",
                hashed_password=hash_password(FIXED_PASSWORD),
            )
            db.add(owner)
            owners.append(owner)
            users.append(owner)

        for _ in range(5):
            user = User(
                username=fake.unique.user_name(),
                firstname=fake.first_name(),
                lastname=fake.last_name(),
                role="reviewer",
                hashed_password=hash_password(FIXED_PASSWORD),
            )
            db.add(user)
            users.append(user)

        await db.commit()

        for u in users:
            await db.refresh(u)

        # -----------------------------
        # BUSINESSES (deterministic owner assignment)
        # -----------------------------
        print("Seeding businesses...")

        businesses = []
        business_vibes = ["improving", "kind_stable", "stable", "declining"]

        for i in range(4):
            business = Business(
                name=fake.company(),
                location=fake.city(),
                short_description=fake.sentence(nb_words=8),
                image_path=None,
                owner_id=owners[i % len(owners)].id
            )

            db.add(business)
            businesses.append(business)

        await db.commit()

        for b in businesses:
            await db.refresh(b)

        # -----------------------------
        # REVIEWS (IMPORTANT FIX: spread time correctly)
        # -----------------------------
        print("Seeding reviews...")

        review_objects = []
        review_meta = []

        reviews_per_business = 40

        for i, business in enumerate(businesses):
            vibe_type = business_vibes[i]

            for j in range(reviews_per_business):
                created_at = generate_created_at_with_bias()

                review_text = generate_review_by_vibe(
                    vibe_type,
                    j,
                    reviews_per_business
                )

                review_meta.append((review_text, business, created_at))

        review_texts = [r[0] for r in review_meta]

        results = analyze_sentiment_batch(review_texts, models.sentiment)

        for (text, business, created_at), (score, label, _) in zip(review_meta, results):
            review = Review(
                content=text,
                sentiment_label=label,
                sentiment_score=score,
                user_id=random.choice(users).id,
                business_id=business.id,
                created_at=created_at,
            )

            db.add(review)
            review_objects.append(review)

        await db.commit()

        for r in review_objects:
            await db.refresh(r)

        # -----------------------------
        # ABSA
        # -----------------------------
        print("Running ABSA...")

        for review in review_objects:
            await run_absa_for_review(db, review, models)

        await db.commit()

        # -----------------------------
        # SNAPSHOTS (THIS IS CORRECT LOGIC)
        # -----------------------------
        print("Creating vibe snapshots...")

        for business in businesses:
            print(f"Backfilling business {business.id}...")
            await backfill_vibe_snapshots(db, business.id, models)

        await db.commit()

        print("Seeding complete!")


# Entry point for running the seed script
if __name__ == "__main__":
    asyncio.run(seed())