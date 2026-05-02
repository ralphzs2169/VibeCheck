# Seed the database with sample data for testing and development.
# Usage: python -m backend.app.scripts.seed

import asyncio
import random
from datetime import datetime, timedelta, timezone

from faker import Faker
from sqlalchemy import func, select

from backend.app.core.database import Base, engine
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


async def get_first_review_date(db, business_id: int):
    result = await db.execute(
        select(func.min(Review.created_at))
        .where(Review.business_id == business_id)
    )
    return result.scalar()


async def backfill_vibe_snapshots(db, business_id: int):
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
            snapshot_date=current
        )
        if snapshot is not None:
            snapshots_created += 1
        current += timedelta(days=1)
    
    if snapshots_created > 0:
        print(f"  Created {snapshots_created} snapshots for business {business_id}")




# def generate_review_with_drift(days_ago: int) -> str:
#     # Simulate review content that changes in style and sentiment based on how long ago it was written.

#     if days_ago > 365:
#         style = random.choice(["simple_positive", "simple_positive", "story"])
#     elif days_ago > 180:
#         style = random.choice(["mixed", "simple_positive", "story"])
#     elif days_ago > 60:
#         style = random.choice(["mixed", "simple_negative"])
#     else:
#         style = random.choice(["simple_negative", "simple_negative", "mixed"])

#     feature = random.choice(FEATURES)
#     pos1, pos2 = random.sample(POSITIVE_ASPECTS, 2)
#     neg = random.choice(NEGATIVE_ASPECTS)

#     if style == "simple_positive":
#         return (
#             f"The {feature} was excellent. "
#             f"We enjoyed {pos1} and {pos2}. Highly recommended."
#         )

#     if style == "simple_negative":
#         return (
#             f"Very disappointing {feature}. "
#             f"We experienced {neg} and poor service overall."
#         )

#     if style == "mixed":
#         return (
#             f"The {feature} had {pos1}, but also {neg}, "
#             f"which affected our experience."
#         )

#     return (
#         f"We stayed at a {feature}. The highlight was {pos1}, "
#         f"but we also faced issues like {neg}. Still memorable overall."
#     )

def get_sentiment_stage(vibe_type: str, progress: float):
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
    # For seeding demo data, distribute reviews evenly across time
    # instead of biasing heavily towards recent dates
    # This ensures we get multiple snapshots per business for better analytics demo
    
    weights = [
        ("-3mo", "-2mo"),
        ("-2mo", "-1mo"),
        ("-1mo", "-2w"),
        ("-2w", "-1w"),
        ("-1w", "now"),
    ]

    # More even distribution for demo purposes
    start, end = random.choices(weights, weights=[1, 1, 1, 1, 1])[0]

    return fake.date_time_between(start_date=start, end_date=end, tzinfo=timezone.utc)


# -----------------------------
# Main seeding function
# -----------------------------
async def seed() -> None:
    async with AsyncSessionLocal() as db:

        # Create tables if they don't exist
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        # Clear existing data
        await db.execute(Review.__table__.delete())
        await db.execute(Business.__table__.delete())
        await db.execute(User.__table__.delete())
        await db.commit()

        # -----------------------------
        # Seed users
        # -----------------------------
        print("Seeding users...")
        users = []

        for _ in range(10):
            user = User(
                username=fake.unique.user_name(),
                firstname=fake.first_name(),
                lastname=fake.last_name(),
            )
            db.add(user)
            users.append(user)

        # -----------------------------
        # Seed businesses
        # -----------------------------
        print("Seeding businesses...")
        businesses = []

        vibe_types = ["improving", "kind_stable", "stable", "declining"]

        for i in range(4):
            business = Business(
                name=fake.company(),
                location=fake.city(),
                short_description=fake.sentence(nb_words=8),
                image_path=None,
            )
            db.add(business)
            businesses.append(business)

            business.vibe_profile = vibe_types[i]


        await db.commit()

        # Refresh IDs
        for user in users:
            await db.refresh(user)
        for business in businesses:
            await db.refresh(business)


        # Seed reviews 
        print("Seeding reviews...")

        review_objects = []
        review_meta = []

        reviews_per_business = 30

        for business in businesses:
            for i in range(reviews_per_business):

                created_at = datetime.now(timezone.utc) - timedelta(days=(reviews_per_business - i))

                review_text = generate_review_by_vibe(
                    business.vibe_profile,
                    i,
                    reviews_per_business
                )

                review_meta.append((review_text, business, created_at))

        review_texts = [r[0] for r in review_meta]

        # sentiment batch
        results = analyze_sentiment_batch(review_texts)

        # Create review objects 
        for (review_text, business, created_at), (score, label, _) in zip(
            review_meta,
            results
        ):
            review = Review(
                content=review_text,
                sentiment_label=label,
                sentiment_score=score,
                user_id=random.choice(users).id,
                business_id=business.id,
                created_at=created_at,
            )

            db.add(review)
            review_objects.append(review)

        await db.commit()

        # IMPORTANT: ensure IDs exist
        for r in review_objects:
            await db.refresh(r)

        print("Running ABSA on seeded reviews...")

        for review in review_objects:
            await run_absa_for_review(db, review)

        await db.commit()


        print("Creating historical vibe snapshots...")

        for business in businesses:
            print(f"Backfilling business {business.id}...")
            await backfill_vibe_snapshots(db, business.id)

        await db.commit()


        await db.commit()

        print("Database seeding complete!")



# Entry point for running the seed script
if __name__ == "__main__":
    asyncio.run(seed())