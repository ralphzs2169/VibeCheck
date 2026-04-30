from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.models.review import Review
from backend.app.schemas.review import ReviewCreate, ReviewResponse, ReviewUpdate
import backend.app.services.review_service as review_service

router = APIRouter()


@router.post(
    "",
    response_model=ReviewResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_review(
    review: ReviewCreate, db: Annotated[AsyncSession, Depends(get_db)]
) -> Review:
    review = await review_service.create_review(db, review)
    return review


@router.get("/{review_id}", response_model=ReviewResponse)
async def get_review(review_id: int, db: AsyncSession = Depends(get_db)) -> Review:
    review = await review_service.get_review_or_404(db, review_id)
    return review


@router.get("", response_model=list[ReviewResponse])
async def get_reviews(db: Annotated[AsyncSession, Depends(get_db)]) -> list[Review]:
    reviews = await review_service.get_all_reviews(db)
    return reviews


@router.patch("/{review_id}", response_model=ReviewResponse)
async def update_review(
    review_id: int,
    updated_review: ReviewUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Review:
    review = await review_service.update_review(db, review_id, updated_review)
    return review


@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_review(
    review_id: int, db: Annotated[AsyncSession, Depends(get_db)]
) -> None:
    await review_service.delete_review(db, review_id)
