from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

import backend.app.services.business_service as business_service
from backend.app.core.database import get_db
from backend.app.models.business import Business
from backend.app.models.vibe_snapshot import VibeSnapshot
from backend.app.schemas.business import (
    BusinessCreate,
    BusinessResponse,
    BusinessUpdate,
    BusinessWithReviewsResponse,
)
from backend.app.schemas.vibe_snapshot import VibeSnapshotResponse

from backend.app.services.analytics_service import AnalyticsService
from backend.app.services.vibe_service import compute_vibe_summary

router = APIRouter()


@router.post(
    "",
    response_model=BusinessResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_business(
    business: BusinessCreate, db: Annotated[AsyncSession, Depends(get_db)]
) -> Business:
    return await business_service.create_business(db, business)


@router.get("/{business_id}", response_model=BusinessResponse)
async def get_business(
    business_id: int, db: Annotated[AsyncSession, Depends(get_db)]
) -> Business:
    business = await business_service.get_business_or_404(db, business_id)
    return business


@router.get("", response_model=list[BusinessResponse])
async def get_businesses(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[Business]:
    businesses = await business_service.get_all_businesses(db)
    return businesses


@router.patch("/{business_id}", response_model=BusinessResponse)
async def update_business(
    business_id: int,
    updated_business: BusinessUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Business:
    return await business_service.update_business(db, business_id, updated_business)


@router.delete("/{business_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_business(
    business_id: int, db: Annotated[AsyncSession, Depends(get_db)]
):
    await business_service.delete_business(db, business_id)


# -------------------------
# BUSINESS REVIEW ROUTES
# -------------------------
@router.get("/{business_id}/reviews", response_model=BusinessWithReviewsResponse)
async def get_business_with_reviews(
    business_id: int, db: Annotated[AsyncSession, Depends(get_db)]
) -> Business:
    return await business_service.get_business_with_reviews(db, business_id)


# -------------------------
# BUSINESS VIBE ROUTES
# -------------------------
@router.get("/vibe/{business_id}")
async def get_business_vibe(
    business_id: int, db: Annotated[AsyncSession, Depends(get_db)]
) -> dict:
    return await business_service.get_business_vibe(db, business_id)


@router.get("/vibe_snapshots/{business_id}", response_model=list[VibeSnapshotResponse])
async def get_business_vibe_snapshots(
    business_id: int, db: Annotated[AsyncSession, Depends(get_db)]
) -> list[VibeSnapshot]:
    return await business_service.get_vibe_snapshots(db, business_id)



# -------------------------
# BUSINESS ANALYTICS ROUTES
# -------------------------
@router.get("/{business_id}/analytics")
@router.get("/{business_id}/dashboard")
async def get_dashboard(
    business_id: int,
    db: AsyncSession = Depends(get_db)
):
    return {
        # -------------------------
        # VIBE LAYER (PRIMARY)
        # -------------------------
        "vibe_summary": await compute_vibe_summary(db, business_id),

        "latest_vibe": await AnalyticsService.get_latest_vibe(db, business_id),
        "vibe_trend": await AnalyticsService.get_vibe_score_trend(db, business_id),
        "vibe_volatility": await AnalyticsService.get_vibe_volatility(db, business_id),

        # optional fallback snapshot summary
        "vibe_history": await business_service.get_vibe_snapshots(db, business_id),
        "vibe_over_time": await AnalyticsService.get_vibe_score_over_time(db, business_id),

         # -------------------------
        # SENTIMENT LAYER (RAW INSIGHTS)
        # -------------------------
        "distribution": await AnalyticsService.get_sentiment_distribution(db, business_id),
        "trend": await AnalyticsService.get_sentiment_trend_slope(db, business_id),
        "volatility": await AnalyticsService.get_sentiment_volatility(db, business_id),
        "peak_drop": await AnalyticsService.get_peak_and_drop(db, business_id),

        "temporal": await AnalyticsService.get_sentiment_over_time(db, business_id, "daily"),
        "forecast": await AnalyticsService.forecast_sentiment(db, business_id),
        "aspects": await AnalyticsService.get_business_aspect_summary(db, business_id),
    }

