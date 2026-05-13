from fastapi import HTTPException, status
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

import backend.app.services.business_service as business_service
import backend.app.services.user_service as user_service
from backend.app.core.ml_registry import MLRegistry
from backend.app.models.aspect_sentiment import AspectSentiment
from backend.app.models.review import Review
from backend.app.schemas.review import ReviewCreate
from backend.app.services.absa_service import run_absa_for_review
from backend.app.services.sentiment_service import analyze_sentiment


async def create_review(db: AsyncSession, review: ReviewCreate,  user_id: int, models: MLRegistry) -> Review:
    existing_user = await user_service.get_user_or_404(db, user_id)
    existing_business = await business_service.get_business_or_404(db, review.business_id)

    sentiment_score, sentiment_label, _ = analyze_sentiment(review.content, models.sentiment)

    new_review = Review(
        content=review.content,
        sentiment_score=sentiment_score,
        sentiment_label=sentiment_label,
        user_id=existing_user.id,
        business_id=existing_business.id,
    )

    db.add(new_review)

    await db.flush()  # ensures new_review.id is populated

    # Apply NLP processing (sentiment + ABSA) before final commit
    await _apply_nlp_and_absa(db, new_review, models)

    await db.commit()
    await db.refresh(new_review)

    # Fetch the review again to include related user and aspect sentiments for the response
    result = await db.execute(
        select(Review)
        .where(Review.id == new_review.id)
        .options(
            selectinload(Review.user),
            selectinload(Review.aspect_sentiments),
        )
    )
    
    return result.scalars().first()


async def get_review_or_404(db: AsyncSession, review_id: int) -> Review:
    result = await db.execute(
        select(Review)
        .where(Review.id == review_id)
        .options(
            selectinload(Review.user),
            selectinload(Review.aspect_sentiments),
        )
    )
    review = result.scalars().first()

    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Review not found"
        )

    return review


async def get_all_reviews(db: AsyncSession):
    result = await db.execute(
        select(Review).options(
            selectinload(Review.user),
            selectinload(Review.aspect_sentiments),
        )
    )
    return result.scalars().all()


async def get_latest_reviews_for_business(db: AsyncSession, business_id: int, limit: int = 5) -> list[Review]:
    result = await db.execute(
        select(Review)
        .where(Review.business_id == business_id)
        .order_by(Review.created_at.desc())
         .options(
            selectinload(Review.user),
            selectinload(Review.aspect_sentiments)
        )
        .limit(limit)
    )
    return result.scalars().all()


async def get_reviews_for_business(db: AsyncSession, business_id: int) -> list[Review]:
    result = await db.execute(
        select(Review)
        .where(Review.business_id == business_id)
        .order_by(Review.created_at.desc())
        .options(
            selectinload(Review.user),
            selectinload(Review.aspect_sentiments),
        )
    )
    return result.scalars().all()


async def get_reviews_for_business_paginated(
    db: AsyncSession,
    business_id: int,
    offset: int = 0,
    limit: int = 20,
) -> tuple[list[Review], int]:
    count_result = await db.execute(
        select(func.count(Review.id)).where(Review.business_id == business_id)
    )
    total_count = int(count_result.scalar() or 0)

    result = await db.execute(
        select(Review)
        .where(Review.business_id == business_id)
        .order_by(Review.created_at.desc())
        .options(
            selectinload(Review.user),
            selectinload(Review.aspect_sentiments),
        )
        .offset(max(offset, 0))
        .limit(max(limit, 1))
    )

    return result.scalars().all(), total_count


async def update_review(db: AsyncSession, review_id: int, updated_review, models: MLRegistry) -> Review:
    review = await get_review_or_404(db, review_id)
    update_data = updated_review.model_dump(exclude_unset=True)

    # Track whether content changed so we know to re-run NLP
    content_changed = False
    for field, value in update_data.items():
        if field == "content" and getattr(review, "content", None) != value:
            content_changed = True
        setattr(review, field, value)

    await db.flush()

    # If content changed and models are available, re-run sentiment analysis + ABSA
    if content_changed and models is not None:
        await _apply_nlp_and_absa(db, review, models)

    await db.commit()
    await db.refresh(review)
    return review


async def _apply_nlp_and_absa(db: AsyncSession, review: Review, models: MLRegistry) -> None:
    """
    Run sentiment analysis and ABSA for a review and attach results to the review instance.
    This helper centralizes the NLP logic so create/update both reuse the same code path.
    The helper does not commit; callers should commit the session after calling this.
    """
    sentiment_score, sentiment_label, _ = analyze_sentiment(review.content, models.sentiment)

    review.sentiment_score = sentiment_score
    review.sentiment_label = sentiment_label

    # Ensure changes are flushed so ABSA can reference review.id
    await db.flush()

    # Delete existing aspect sentiments before re-running ABSA.
    # This ensures a fresh analysis without stale aspect data when updating reviews.
    delete_stmt = delete(AspectSentiment).where(AspectSentiment.review_id == review.id)
    await db.execute(delete_stmt)
    await db.flush()

    await run_absa_for_review(db, review, models)


async def delete_review(db: AsyncSession, review_id: int):
    review = await get_review_or_404(db, review_id)

    await db.delete(review)
    await db.commit()
