from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.services.analytics_service import AnalyticsService

router = APIRouter()


@router.get("/business/{business_id}/temporal")
async def get_temporal_analytics(
    business_id: int,
    granularity: str = "daily",
    db: AsyncSession = Depends(get_db),
):
    return await AnalyticsService.get_temporal_aggregation(
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