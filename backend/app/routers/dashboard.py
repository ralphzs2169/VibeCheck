from fastapi import APIRouter, Depends

from sqlalchemy.ext.asyncio import AsyncSession
import backend.app.services.auth_service as auth_service
from backend.app.core.database import get_db
from backend.app.models.user import User
from backend.app.services import business_service, review_service
from backend.app.core.ml_registry import MLRegistry
from backend.app.core.dependencies import get_models
from backend.app.core.constants import VIBE_UI_MAP

from backend.app.services.analytics.health_score_analytics import compute_business_health
from backend.app.services.analytics.sentiment_analytics import (
    get_sentiment_over_time,
    get_sentiment_distribution
)

from backend.app.services.analytics.vibe_analytics import (
    get_vibe_score_over_time,
    get_vibe_score_trend,
    get_latest_vibe,
    forecast_vibe_score,
    get_peak_and_drop
)

from backend.app.services.analytics.aspect_analytics import (
    get_aspect_summary,
    get_aspect_trends,
    get_aspect_frequency
)

from backend.app.services.analytics.review_analytics import (
    get_review_activity
)

from backend.app.services.insights_service import (
    get_positive_drivers
)

router = APIRouter()

@router.get("")
async def get_dashboard(
    business_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(auth_service.get_authenticated_user),
    models: MLRegistry = Depends(get_models),
):
    """
        Dashboard endpoint that aggregates all necessary data for the business owner dashboard in a single call. This includes:
    """

    if business_id is None:
        # if business_id is not provided, resolve it from the authenticated user's business
        business_id = business_service.resolve_user_business_id(
            current_user,
            business_id
        )


    # security check
    await business_service.verify_business_ownership(
        db,
        business_id,
        current_user.id
    )

    profile = await business_service.get_business_by_id(db, business_id)

    # ===================
    # Card Metrics
    # ===================
    # (CARD 1) Vibe Score with trend (stable, improving or declining)
    latest_vibe = await get_latest_vibe(db, business_id)
    vibe_score_trend = await get_vibe_score_trend(db, business_id)
    
    # (CARD 2) Review Count
    review_count = await business_service.get_business_review_count(db, business_id)

    # (CARD 3) Top Performing Aspect 
    aspect_summary = await get_aspect_summary(db, business_id)
    aspect_trends = await get_aspect_trends(db, business_id)
    # Top Performing ASPECT is derived from get_positive_drivers which takes into account both the aspect summary
    #  and trends, as well as review volume, to identify which aspect is currently the strongest driver of positive sentiment for the business
    positive_drivers = get_positive_drivers(
        aspect_summary["summary"],
        aspect_trends["trends"],
        review_count,
    )

    # ======================================
    # Business Health Gauge or Compass ba ron
    # ======================================
    business_health = await compute_business_health(
        vibe_score=latest_vibe.get("vibe_score", 0),
        trend=vibe_score_trend.get("trend", "stable"),
        aspects=aspect_summary["summary"],
        review_count=review_count
    )

    # =====================================
    # Review Activity
    # =====================================
    # Detect if there are any significant changes in review volume or sentiment in the last 7 days 
    # compared to the previous period, which could indicate a PR crisis or viral growth
    review_activity = await get_review_activity(db, business_id)


    # ====================================================================
    # Vibe Performance Over Time Line Chart with Peak and Drop Annotations
    # ====================================================================
    # filter by daily, weekly and monthly
    vibe_score_daily = await get_vibe_score_over_time(db, business_id, "daily")
    vibe_score_weekly = await get_vibe_score_over_time(db, business_id, "weekly")
    vibe_score_monthly = await get_vibe_score_over_time(db, business_id, "monthly")

    # Peak - Strongest Positive Change in Vibe Score
    # Drop - Strongest Negative Change in Vibe Score
    peak_and_drop = await get_peak_and_drop(db, business_id)

    # =====================================
    # Aspect Frequency Share Pie Chart
    # =====================================
    aspect_frequency = await get_aspect_frequency(
        db=db,
        business_id=business_id,
        aspects=aspect_summary,
    )

    # ====================================
    # Sentiment Distribution Pie Chart
    # =====================================
    sentiment_distribution = await get_sentiment_distribution(db, business_id)

    # =====================================
    # Sentiment Over Time Line Chart
    # =====================================
    sentiment_over_time = await get_sentiment_over_time(db, business_id, "daily")

    # =====================================
    # Vibe Score Forecast with Line Chart
    # =====================================
    forecast_vibe =  await forecast_vibe_score(db, business_id)

    # ===========================
    # Latest Reviews 
    # ===========================
    latest_reviews = await review_service.get_latest_reviews_for_business(db, business_id, limit=5)
    
    
    # Dont mind the vibe_ui mapping - this is just to derive the appropriate UI label and color for the vibe card
    # derive UI label and type for vibe card based on latest vibe label
    label = latest_vibe.get("vibe_label") if latest_vibe else None
    label_key = label.lower() if label else None

    return {

        "profile": profile,
        "business_health": business_health,
        "review_count": review_count,
         
        "positive_drivers": positive_drivers,
        "vibe": latest_vibe,
        "vibe_ui": VIBE_UI_MAP.get(label_key),
        "vibe_score_trend": vibe_score_trend,

        "peak_and_drop": peak_and_drop,

        "review_activity": review_activity,

        "sentiment_over_time": sentiment_over_time,
        "sentiment_distribution": sentiment_distribution,


        "forecast_vibe": forecast_vibe,
        # CHART DATA (VibeChart)
        "vibe_chart": {
            "7D": vibe_score_daily["data"],
            "30D": vibe_score_weekly["data"],
            "90D": vibe_score_monthly["data"],
        },

        "latest_reviews":  latest_reviews,
        "aspect_frequency": aspect_frequency
    }