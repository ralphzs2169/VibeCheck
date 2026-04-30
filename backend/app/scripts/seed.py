# Seed the database with sample data for testing and development.
# Usage: python -m backend.app.scripts.seed

import asyncio
import random

from faker import Faker

from backend.app.services.sentiment_service import analyze_sentiment
from ..core.database import AsyncSessionLocal
from ..models.user import User
from ..models.business import Business
from ..models.review import Review

fake = Faker()

# Review generation logic with more realistic patterns and diversity
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


def generate_review() -> str:
    feature = random.choice(FEATURES)
    pos1, pos2 = random.sample(POSITIVE_ASPECTS, 2)
    neg = random.choice(NEGATIVE_ASPECTS)

    style = random.choice(["simple_positive", "simple_negative", "mixed", "story"])

    if style == "simple_positive":
        return (
            f"The {feature} was excellent. "
            f"We enjoyed {pos1} and {pos2}. Highly recommended."
        )

    elif style == "simple_negative":
        return (
            f"Very disappointing {feature}. "
            f"We experienced {neg} and poor service overall."
        )

    elif style == "mixed":
        return (
            f"The {feature} had {pos1}, "
            f"but also {neg}, which affected our experience."
        )

    else:  
        return (
            f"We stayed at a {feature} last weekend. "
            f"The highlight was {pos1}, especially the {pos2}. "
            f"However, we also faced issues like {neg}. "
            f"Still, it was a memorable trip overall."
        )


def generate_reviews(n: int = 100) -> list[str]:
    return [generate_review() for _ in range(n)]



async def seed() -> None:

    async with AsyncSessionLocal() as db:

        # Clear existing data
        await db.execute(Review.__table__.delete())
        await db.execute(Business.__table__.delete())
        await db.execute(User.__table__.delete())
        await db.commit()

        # Seed users
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

        # Seed businesses
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

        # Refresh to get DB-assigned IDs
        for user in users:
            await db.refresh(user)
        for business in businesses:
            await db.refresh(business)

        # Seed reviews
        print("Seeding reviews...")
        for i in range(120): # 120 reviews for more robust testing
            review_text = generate_review()
            polarity_score, sentiment_label, confidence = analyze_sentiment(review_text)

            review = Review(
                content=review_text,
                sentiment_label=sentiment_label,
                sentiment_score=polarity_score,
                user_id=random.choice(users).id,
                business_id=random.choice(businesses).id,
                created_at=fake.date_time_this_year(),
            )
            db.add(review)

            if (i + 1) % 20 == 0:
                print(f"   {i + 1}/120 reviews seeded...")

        await db.commit()
        print("Database seeding complete!")

if __name__ == "__main__":
    asyncio.run(seed())