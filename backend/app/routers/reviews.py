from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload


from backend.app.schemas import user
from backend.app.schemas.review import ReviewCreate, ReviewResponse, ReviewUpdate

from backend.app.models.review import Review
from backend.app.core.database import get_db

from backend.app.services.review_service import get_review_or_404
from backend.app.services.user_service import get_user_or_404
from backend.app.services.business_service import get_business_or_404
# from backend.app.services.sentiment_service import analyze_sentiment

router = APIRouter()


# Create Review
@router.post(
    "", 
    response_model=ReviewResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_review(review: ReviewCreate, db: Annotated[AsyncSession, Depends(get_db)]):

    # Validate user and business existence
    existing_user = await get_user_or_404(db, review.user_id)
    existing_business = await get_business_or_404(db, review.business_id)

    # Analyze sentiment
    # sentiment_result = analyze_sentiment(review.content)

    new_review = Review(
        content=review.content,
        sentiment_score=0.5,
        sentiment_label=0.5,

        user_id=existing_user.id,
        business_id=existing_business.id,
    )

    db.add(new_review)
    await db.commit()
    await db.refresh(new_review)
    return new_review


# Get Review by ID
@router.get("/{review_id}", response_model=ReviewResponse)
async def get_review(
    review_id: int,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    review = await get_review_or_404(db, review_id)
    return review


# Get all Reviews
@router.get("", response_model=list[ReviewResponse])
async def get_reviews(db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
        select(Review).options(selectinload(Review.user), selectinload(Review.business))
    )
    reviews = result.scalars().all()
    return reviews


# Update Review
@router.patch("/{review_id}", response_model=ReviewResponse)
async def update_review(
    review_id: int,
    updated_review: ReviewUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    review = await get_review_or_404(db, review_id)

    update_data = updated_review.model_dump(exclude_unset=True)

    # Apply updates safely
    for field, value in update_data.items():
        setattr(review, field, value)

    await db.commit()
    await db.refresh(review)

    return review


# Delete Review
@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_review(review_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    review = await get_review_or_404(db, review_id)

    await db.delete(review)
    await db.commit()