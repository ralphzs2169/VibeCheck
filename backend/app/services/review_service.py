from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


import backend.app.services.business_service as business_service
import backend.app.services.user_service as user_service
from backend.app.models.review import Review
from backend.app.services.sentiment_service import analyze_sentiment
from backend.app.services.vibe_snapshot_service import create_vibe_snapshot


async def create_review(db: AsyncSession, review) -> Review:
    existing_user = await user_service.get_user_or_404(db, review.user_id)
    existing_business = await business_service.get_business_or_404(db, review.business_id)

    sentiment_score, sentiment_label, _ = analyze_sentiment(review.content)

    new_review = Review(
        content=review.content,
        sentiment_score=sentiment_score,
        sentiment_label=sentiment_label,
        user_id=existing_user.id,
        business_id=existing_business.id,
    )

    db.add(new_review)
    await db.commit()
    await db.refresh(new_review)

    await create_vibe_snapshot(db, review.business_id)
    
    return new_review


async def get_review_or_404(db: AsyncSession, review_id: int) -> Review:
    result = await db.execute(select(Review).where(Review.id == review_id))
    review = result.scalars().first()

    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Review not found"
        )

    return review


async def get_all_reviews(db: AsyncSession):
    result = await db.execute(select(Review))
    return result.scalars().all()


async def update_review(db: AsyncSession, review_id: int, updated_review):
    review = await get_review_or_404(db, review_id)

    update_data = updated_review.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(review, field, value)

    await db.commit()
    await db.refresh(review)
    return review


async def delete_review(db: AsyncSession, review_id: int):
    review = await get_review_or_404(db, review_id)

    await db.delete(review)
    await db.commit()
