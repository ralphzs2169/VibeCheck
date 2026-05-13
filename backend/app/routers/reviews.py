from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

import backend.app.services.auth_service as auth_service
import backend.app.services.review_service as review_service
from backend.app.core.authorization import validate_owner
from backend.app.core.database import get_db
from backend.app.models.review import Review
from backend.app.models.user import User
from backend.app.schemas.aspect_sentiment import AspectSentimentResponse
from backend.app.schemas.review import ReviewCreate, ReviewResponse, ReviewUpdate
from backend.app.services.absa_service import get_review_aspects

router = APIRouter()


@router.post(
    "",
    response_model=ReviewResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_review(
    review: ReviewCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    request: Request,
    current_user: User = Depends(auth_service.get_authenticated_user),
):
    models = request.app.state.models

    new_review = await review_service.create_review(
        db=db,
        review=review,
        user_id=current_user.id, 
        models=models,
    )

    return new_review


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
    request: Request,
    current_user: User = Depends(auth_service.get_authenticated_user),
) -> Review:
    review = await review_service.get_review_or_404(db, review_id)

    validate_owner(current_user, review.user_id)

    models = request.app.state.models

    return await review_service.update_review(
        db,
        review_id,
        updated_review,
        models=models,
    )


@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_review(
    review_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: User = Depends(auth_service.get_authenticated_user),
) -> None:
    review = await review_service.get_review_or_404(db, review_id)

    validate_owner(current_user, review.user_id)

    await review_service.delete_review(db, review_id)


@router.get("/{review_id}/aspects",response_model=list[AspectSentimentResponse])
async def get_review_aspects_route(
    review_id: int,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    return await get_review_aspects(db, review_id)