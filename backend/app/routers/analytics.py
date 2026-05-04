from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.services import vibe_service
from backend.app.services.analytics_service import AnalyticsService

router = APIRouter()


@router.get("/business/{business_id}/sentiment-over-time")
async def get_sentiment_over_time(
    business_id: int,
    granularity: str = "daily",
    db: AsyncSession = Depends(get_db),
):
    return await AnalyticsService.get_sentiment_over_time(
        db,
        business_id,
        granularity
    )


@router.get("/business/{business_id}/distribution")
async def get_sentiment_distribution(
    business_id: int,
    db: AsyncSession = Depends(get_db),
):
    return await AnalyticsService.get_sentiment_distribution(
        db,
        business_id
    )


@router.get("/business/{business_id}/trend")
async def get_sentiment_trend(
    business_id: int,
    db: AsyncSession = Depends(get_db),
):
    return await AnalyticsService.get_sentiment_trend_slope(
        db,
        business_id
    )


@router.get("/business/{business_id}/volatility")
async def get_sentiment_volatility(
    business_id: int,
    db: AsyncSession = Depends(get_db),
):
    return await AnalyticsService.get_sentiment_volatility(
        db,
        business_id
    )


@router.get("/business/{business_id}/peak-drop")
async def get_peak_and_drop(
    business_id: int,
    db: AsyncSession = Depends(get_db),
):
    return await AnalyticsService.get_peak_and_drop(
        db,
        business_id
    )


@router.get("/business/{business_id}/forecast")
async def get_forecast(
    business_id: int,
    db: AsyncSession = Depends(get_db)
):
    return await AnalyticsService.forecast_sentiment(db, business_id)


@router.get("/business/{business_id}/aspects")
async def get_aspect_summary(
    business_id: int,
    db: AsyncSession = Depends(get_db)
):
    return await AnalyticsService.get_business_aspect_summary(db, business_id)


@router.get("/business/{business_id}/vibe_summary")
async def get_vibe_summary(
    business_id: int,
    db: AsyncSession = Depends(get_db),
    request: Request = None
):
    models = request.app.state.models if request else None
    return await vibe_service.compute_vibe_summary(db, business_id, models)

@router.get("/business/{business_id}/vibe_over_time")
async def get_vibe_score_over_time(
    business_id: int,
    db: AsyncSession = Depends(get_db)
):
    return await AnalyticsService.get_vibe_score_over_time(db, business_id)


@router.get("/business/{business_id}/vibe_trend")
async def get_vibe_score_trend(
    business_id: int,
    db: AsyncSession = Depends(get_db)
):
    return await AnalyticsService.get_vibe_score_trend(db, business_id)


@router.get("/business/{business_id}/vibe_volatility")
async def get_vibe_score_volatility(
    business_id: int,
    db: AsyncSession = Depends(get_db)
):
    return await AnalyticsService.get_vibe_volatility(db, business_id)  


@router.get("/business/{business_id}/latest_vibe")
async def get_latest_vibe(
    business_id: int,
    db: AsyncSession = Depends(get_db)
):
    return await AnalyticsService.get_latest_vibe(db, business_id)