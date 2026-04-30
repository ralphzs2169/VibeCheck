# Seed the database with sample data for testing and development.
# Usage: python -m backend.app.scripts.seed

import asyncio
import random
from datetime import datetime, timezone

from faker import Faker

from backend.app.core.database import Base, engine
from backend.app.services.sentiment_service import analyze_sentiment_batch

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



def generate_review_with_drift(days_ago: int) -> str:
    # Simulate review content that changes in style and sentiment based on how long ago it was written.

    if days_ago > 365:
        style = random.choice(["simple_positive", "simple_positive", "story"])
    elif days_ago > 180:
        style = random.choice(["mixed", "simple_positive", "story"])
    elif days_ago > 60:
        style = random.choice(["mixed", "simple_negative"])
    else:
        style = random.choice(["simple_negative", "simple_negative", "mixed"])

    feature = random.choice(FEATURES)
    pos1, pos2 = random.sample(POSITIVE_ASPECTS, 2)
    neg = random.choice(NEGATIVE_ASPECTS)

    if style == "simple_positive":
        return (
            f"The {feature} was excellent. "
            f"We enjoyed {pos1} and {pos2}. Highly recommended."
        )

    if style == "simple_negative":
        return (
            f"Very disappointing {feature}. "
            f"We experienced {neg} and poor service overall."
        )

    if style == "mixed":
        return (
            f"The {feature} had {pos1}, but also {neg}, "
            f"which affected our experience."
        )

    return (
        f"We stayed at a {feature}. The highlight was {pos1}, "
        f"but we also faced issues like {neg}. Still memorable overall."
    )



def generate_created_at_with_bias() -> datetime:
    # Bias towards more recent dates to simulate real-world review patterns
    weights = [
        ("-2y", "-1y"),
        ("-1y", "-6mo"),
        ("-6mo", "-1mo"),
        ("-1mo", "now"),
    ]

    # Randomly select a time range based on weights (more recent ranges are more likely)
    start, end = random.choices(weights, weights=[1, 2, 3, 4])[0]

    return fake.date_time_between(start_date=start, end_date=end, tzinfo=timezone.utc)


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

        for _ in range(5):
            business = Business(
                name=fake.company(),
                location=fake.city(),
                short_description=fake.sentence(nb_words=8),
                image_path=None,
            )
            db.add(business)
            businesses.append(business)

        await db.commit()

        # Refresh IDs
        for user in users:
            await db.refresh(user)
        for business in businesses:
            await db.refresh(business)


        # Seed reviews 
        print("Seeding reviews...")

        review_texts = []
        review_meta = []

        for i in range(120):
            business = random.choice(businesses)

            created_at = generate_created_at_with_bias()
            days_ago = (datetime.now(timezone.utc) - created_at).days

            review_text = generate_review_with_drift(days_ago)

            review_texts.append(review_text)
            review_meta.append((business, created_at))

        results = analyze_sentiment_batch(review_texts)

        # Build Review objects using batch results
        for (review_text, (business, created_at)), (score, label, _) in zip(
            zip(review_texts, review_meta),
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

        await db.commit()
        print("Database seeding complete!")



# Entry point for running the seed script
if __name__ == "__main__":
    asyncio.run(seed())