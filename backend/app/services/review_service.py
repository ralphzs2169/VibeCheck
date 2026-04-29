from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from backend.app.models.review import Review

async def get_review_or_404(db: AsyncSession, review_id: int):
    result = await db.execute(
        select(Review).where(Review.id == review_id)
    )
    review = result.scalars().first()

    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found",
        )

    return review