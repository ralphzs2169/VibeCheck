from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

import backend.app.services.auth_service as auth_service
from backend.app.core.database import get_db
from backend.app.models.user import User
from backend.app.services import business_service, insights_service
from backend.app.services.analytics.aspect_analytics import (
    get_aspect_summary,
    get_aspect_trends,
    get_aspect_frequency,
)
from backend.app.services.analytics.health_score_analytics import (
    compute_business_health,
)
from backend.app.services.analytics.sentiment_analytics import get_sentiment_volatility
                                                                
from backend.app.services.analytics.vibe_analytics import (
    get_latest_vibe,
    get_vibe_score_trend,
    get_vibe_score_over_time,
    get_vibe_volatility,
    forecast_vibe_score,
    get_peak_and_drop,
)

from backend.app.services.analytics.review_analytics import (
    get_review_activity,
    get_review_velocity,
)

router = APIRouter()

@router.get("")
async def get_analytics(
    business_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(auth_service.get_authenticated_user),
):
    """
    Main analytics endpoint that aggregates various insights for a business dashboard.
    """
    # If business_id is not provided, resolve it from the authenticated user's business
    business_id = business_service.resolve_user_business_id(
        current_user,
        business_id
    )

    # verify ownership before doing any analytics work
    await business_service.verify_business_ownership(
        db,
        business_id,
        current_user.id
    )
    review_count = await business_service.get_business_review_count(db, business_id)

    # =====================================
    # Metric Cards and Summary Stats
    # =====================================
    # (CARD 1) Data Quality, a threshold metric to indicate if there's enough data to generate 
    #          reliable insights, based on review count and recency
    #         - No separate function; Derived from business health computation

    # (CARD 2) Feedback Consisteny
    sentiment_volatility = await get_sentiment_volatility(db, business_id)

    # (CARD 2b) Vibe volatility for consistency / signal stability
    vibe_volatility = await get_vibe_volatility(db, business_id)

    # (CARD 3) Vibe Trend Direction (improving, declining, stable)
    vibe_score_trend = await get_vibe_score_trend(db, business_id)

    # =====================================
    # Aspect Health Summary with Trends 
    # =====================================
    aspect_summary = await get_aspect_summary(db, business_id)
    aspect_trends = await get_aspect_trends(db, business_id)

    # =====================================
    # Aspect Frequency Bar Chart
    # =====================================
    aspect_frequency = await get_aspect_frequency(
        db=db,
        business_id=business_id,
        aspects=aspect_summary,
    )

    # Loop through aspects to build a list of aspect details including trend data for frontend display
    aspects = [
        {
            "name": aspect_name,
            "score": aspect_data["avg_score"],
            "label": aspect_data["label"],
            "trend": aspect_trends["trends"].get(aspect_name, {}).get("trend", "stable"),
            "change": aspect_trends["trends"].get(aspect_name, {}).get("change", 0),
        }
        for aspect_name, aspect_data in aspect_summary["summary"].items()
    ]

    # =====================================
    # Vibe Score Heatmap
    # =====================================
    vibe_score_daily = await get_vibe_score_over_time(db, business_id, "daily")
    vibe_score_weekly = await get_vibe_score_over_time(db, business_id, "weekly")
    vibe_score_monthly = await get_vibe_score_over_time(db, business_id, "monthly")

    # =================================
    # Primary Risk Driver Insight
    # =================================
    primary_risk_driver = insights_service.get_primary_risk_driver(
        aspect_summary=aspect_summary["summary"],
        aspect_trends=aspect_trends["trends"],
        review_count=review_count
    )

    # ================================
    # Positive Drivers Insight
    # ================================
    positive_drivers = insights_service.get_positive_drivers(
        aspect_summary=aspect_summary["summary"],
        aspect_trends=aspect_trends["trends"],
        review_count=review_count
    )

    # =================================
    # Negative Signals Insight
    # ================================
    review_activity = await get_review_activity(db, business_id)
    try:
        review_velocity = await get_review_velocity(db, business_id)
    except AttributeError:
        review_velocity = {
            "status": "insufficient_data",
            "window_days": 30,
            "recent_count": 0,
            "previous_count": 0,
            "recent_per_week": 0.0,
            "previous_per_week": 0.0,
            "change_pct": None,
            "meta": {"is_reliable": False, "sample_size": 0, "min_required": 5},
        }
    negative_signals = insights_service.get_negative_signals(
        aspect_summary=aspect_summary["summary"],
        aspect_trends=aspect_trends["trends"],
        vibe_trend=vibe_score_trend,
        sentiment_volatility=sentiment_volatility,
        event_detection=review_activity
    )


    # Fed into business health computation
    latest_vibe = await  get_latest_vibe(db, business_id)
    # =====================================
    # Business Health Diagnostic Section
    # =====================================
    business_health = await compute_business_health(
        vibe_score=latest_vibe.get("vibe_score", 0),
        trend=vibe_score_trend.get("trend", "stable"),
        aspects=aspect_summary["summary"],
        review_count=review_count
    )

    return {
        "review_count": review_count,
        "latest_vibe": latest_vibe,

        "business_health": business_health,
        "primary_risk_driver": primary_risk_driver,
        "negative_signals": negative_signals,
        "positive_drivers": positive_drivers,
        "aspect_frequency": aspect_frequency,
     
        "vibe_score_daily": vibe_score_daily,      # for heatmap visualization
        "vibe_score_weekly": vibe_score_weekly,    # for weekly trends
        "vibe_score_monthly": vibe_score_monthly,  # for monthly trends
        "sentiment_volatility": sentiment_volatility,
        "vibe_volatility": vibe_volatility,
        "review_velocity": review_velocity,

        "aspects": aspects,
    }