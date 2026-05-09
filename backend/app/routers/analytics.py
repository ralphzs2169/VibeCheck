from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

import backend.app.services.auth_service as auth_service
from backend.app.core.database import get_db
from backend.app.models.user import User
from backend.app.services import business_service, insights_service
from backend.app.services.analytics.aspect_analytics import (
    get_business_aspect_summary,
    get_frequent_aspect_mining,
)
from backend.app.services.analytics.health_score_analytics import (
    compute_business_health,
)
from backend.app.services.analytics.sentiment_analytics import (
    get_sentiment_volatility,
    get_peak_and_drop
                                                                )
from backend.app.services.analytics.vibe_analytics import (
    forecast_vibe_score,
    get_latest_vibe,
    get_vibe_score_trend,
    get_vibe_volatility,
)
from backend.app.services.analytics.review_analytics import get_review_event_detection

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
    review_event_detection = await get_review_event_detection(db, business_id)

    vibe_score_trend = await get_vibe_score_trend(db, business_id)
    latest_vibe = await  get_latest_vibe(db, business_id)
    
    # ABSA Analytics
    aspects = await get_business_aspect_summary(db, business_id)
    frequent_aspect_mining = await get_frequent_aspect_mining(
        db=db,
        business_id=business_id,
        aspects=aspects,
    )

    # Compute overall business health score based on vibe score, trends, aspect performance, and review volume
    business_health = await compute_business_health(
        vibe_score=latest_vibe.get("vibe_score", 0),
        trend=vibe_score_trend.get("trend", "stable"),
        aspects=aspects["summary"],
        review_count=review_count
    )

    # Stability metrics
    sentiment_volatility = await get_sentiment_volatility(db, business_id)
    vibe_volatility = await get_vibe_volatility(db, business_id)

    return {
        "review_count": review_count,
        "latest_vibe": latest_vibe,
        "business_health": business_health,
        "primary_risk_driver": insights_service.get_primary_risk_driver(
            aspect_summary=aspects["summary"], aspect_trends=aspects["trends"], review_count=review_count
        ),

        "negative_signals": insights_service.get_negative_signals(
            aspect_summary=aspects["summary"],
            aspect_trends=aspects["trends"],
            vibe_trend=vibe_score_trend,
            sentiment_volatility=sentiment_volatility,
            event_detection=review_event_detection
        ),

        "positive_drivers": insights_service.get_positive_drivers(
            aspect_summary=aspects["summary"],
            aspect_trends=aspects["trends"],
            review_count=review_count
        ),

        "aspect_intelligence": insights_service.compute_aspect_intelligence(
            aspect_summary=aspects["summary"], aspect_trends=aspects["trends"],
            sentiment_volatility=sentiment_volatility
        ),
        "review_event_detection": review_event_detection,

        "frequent_aspect_mining": frequent_aspect_mining,
        "forecast_vibe": await forecast_vibe_score(db, business_id),
        "peak_and_drop": await get_peak_and_drop(db, business_id),
        "vibe_volatility": vibe_volatility,
        "sentiment_volatility": sentiment_volatility
    }