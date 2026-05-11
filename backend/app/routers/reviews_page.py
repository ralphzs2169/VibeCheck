from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

import backend.app.services.auth_service as auth_service
import backend.app.services.business_service as business_service
import backend.app.services.review_service as review_service
from backend.app.core.database import get_db
from backend.app.core.dependencies import get_models
from backend.app.core.ml_registry import MLRegistry
from backend.app.models.user import User
from backend.app.services.vibe_service import compute_vibe_keywords

router = APIRouter()


@router.get("")
async def get_reviews_page(
    business_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(auth_service.get_authenticated_user),
    models: MLRegistry = Depends(get_models),
):
    resolved_business_id = business_service.resolve_user_business_id(
        current_user,
        business_id,
    )

    await business_service.verify_business_ownership(
        db,
        resolved_business_id,
        current_user.id,
    )

    reviews = await review_service.get_reviews_for_business(db, resolved_business_id)
    keywords = await compute_vibe_keywords(
        db,
        resolved_business_id,
        models,
        allow_insufficient_data=True,
    )

    return {
        "business_id": resolved_business_id,
        "review_count": len(reviews),
        "reviews": reviews,
        "positive_keywords": keywords.get("positive_keywords", []),
        "negative_keywords": keywords.get("negative_keywords", []),
    }