# Run this script to seed the database with sample data for testing and development.
# python -m backend.app.scripts.seed 

import asyncio
import random
from faker import Faker

from ..core.database import AsyncSessionLocal
from ..models.user import User
from ..models.business import Business
from ..models.review import Review

fake = Faker()


async def seed():
    async with AsyncSessionLocal() as db:

        # Clear existing data
        await db.execute(Review.__table__.delete())
        await db.execute(Business.__table__.delete())
        await db.execute(User.__table__.delete())
        await db.commit()

        users = []
        businesses = []

        # Seed users
        for _ in range(10):
            user = User(
                username=fake.unique.user_name(),
                firstname=fake.first_name(),
                lastname=fake.last_name(),
            )
            db.add(user)
            users.append(user)

        # Seed businesses
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

        # refresh to get IDs
        for user in users:
            await db.refresh(user)

        for business in businesses:
            await db.refresh(business)

        # Seed reviews
        sentiments = [
            ("positive", 0.92),
            ("neutral", 0.61),
            ("negative", 0.14),
        ]

        for _ in range(50):
            label, score = random.choice(sentiments)

            review = Review(
                content=fake.paragraph(nb_sentences=3),
                sentiment_label=label,
                sentiment_score=score,
                user_id=random.choice(users).id,
                business_id=random.choice(businesses).id,
                created_at=fake.date_time_this_year(),
            )
            db.add(review)

        await db.commit()


if __name__ == "__main__":
    asyncio.run(seed())