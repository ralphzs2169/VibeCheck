import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.constants import VIBE_UI_MAP
from backend.app.models.user import User
from backend.app.services import auth_service, review_service
import backend.app.services.business_service as business_service
from backend.app.core.database import get_db
from backend.app.core.dependencies import get_models
from backend.app.core.ml_registry import MLRegistry
from backend.app.models.business import Business
from backend.app.schemas.business import (
    BusinessCreate,
    BusinessResponse,
    BusinessUpdate
)
from backend.app.schemas.vibe_snapshot import VibeSnapshotResponse
from backend.app.services.analytics_service import AnalyticsService

router = APIRouter()


# -------------------------
# CREATE BUSINESS
# -------------------------
@router.post(
    "",
    response_model=BusinessResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_business(
    business: BusinessCreate, db: Annotated[AsyncSession, Depends(get_db)]
) -> Business:
    return await business_service.create_business(db, business)


# -------------------------
# GET ALL BUSINESSES
# -------------------------
@router.get("")
async def get_businesses(
    db: Annotated[AsyncSession, Depends(get_db)],
    include_vibe: bool = True
):
    if include_vibe:
        return await business_service.get_all_businesses_with_latest_vibe(db)
    businesses = await business_service.get_all_businesses(db)
    return [BusinessResponse.model_validate(b) for b in businesses]


# -------------------------
# BUSINESS VIBE ROUTES (SPECIFIC PATHS FIRST)
# -------------------------
# @router.get("/vibe/{business_id}")
# async def get_business_latest_vibe(
#     business_id: int, 
#     db: Annotated[AsyncSession, Depends(get_db)],
#     request: Request
# ) -> dict:
#     models = request.app.state.models
#     return await business_service.get_business_latest_vibe(db, business_id, models)


@router.get("/vibe_snapshots/{business_id}", response_model=list[VibeSnapshotResponse])
async def get_business_vibe_snapshots(
    business_id: int, db: Annotated[AsyncSession, Depends(get_db)]
) -> list[VibeSnapshotResponse]:
    snapshots = await business_service.get_business_vibe_snapshots(db, business_id)
    return [
        VibeSnapshotResponse.model_validate(s)
        for s in snapshots
    ]


@router.post("/vibe-snapshots/run/{business_id}")
async def run_snapshot(
    business_id: int,
    db: AsyncSession = Depends(get_db),
    models: MLRegistry = Depends(get_models)
):
    now = datetime.datetime.now(datetime.timezone.utc)
    snapshot = await business_service.run_vibe_snapshot_pipeline(
        db=db,
        business_id=business_id,
        models=models,
        snapshot_date=now
    )
    return snapshot


# -------------------------
# BUSINESS REVIEW ROUTES
# -------------------------
@router.get("/{business_id}/profile", response_model=BusinessResponse)
async def get_business_profile(
    business_id: int, db: Annotated[AsyncSession, Depends(get_db)]
) -> Business:
    return await business_service.get_business_profile(db, business_id)


# -------------------------
# BUSINESS ANALYTICS ROUTES
# -------------------------
@router.get("/dashboard")
async def get_dashboard(
    business_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(auth_service.get_authenticated_user),
):

    if business_id is None:
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

    # -------------------------
    # CARD METRICS
    # -------------------------
    latest_vibe = await AnalyticsService.get_latest_vibe(db, business_id)
    vibe_score_trend = await AnalyticsService.get_vibe_score_trend(db, business_id)
    spike_analysis = await AnalyticsService.get_review_event_detection(db, business_id)

    # -------------------------
    # CHART DATA (FOR VIBECHART)
    # -------------------------
    vibe_score_daily = await AnalyticsService.get_vibe_score_over_time(db, business_id, "daily")
    vibe_score_weekly = await AnalyticsService.get_vibe_score_over_time(db, business_id, "weekly")
    vibe_score_monthly = await AnalyticsService.get_vibe_score_over_time(db, business_id, "monthly")

    # -------------------------
    # ASPECT ANALYTICS
    # -------------------------
    aspects = await AnalyticsService.get_business_aspect_summary(db, business_id)

    # derive UI label and type for vibe card based on latest vibe label
    label = latest_vibe.get("vibe_label") if latest_vibe else None
    label_key = label.lower() if label else None

    review_count = await business_service.get_business_review_count(db, business_id)
    business_health = await AnalyticsService.compute_business_health(
        vibe_score=latest_vibe.get("vibe_score", 0),
        trend=vibe_score_trend.get("trend", "stable"),
        aspects=aspects["summary"],
        review_count=review_count
    )

    return {
        # PROFILE
        "profile": profile,
        "business_health": business_health,
        "review_count": review_count,
        # CARDS
        "vibe": latest_vibe,
        "vibe_ui": VIBE_UI_MAP.get(label_key),
        "vibe_score_trend": vibe_score_trend,
        "spike_analysis": spike_analysis,

        "get_sentiment_over_time": await AnalyticsService.get_sentiment_over_time(db, business_id, "daily"),
        "get_sentiment_distribution": await AnalyticsService.get_sentiment_distribution(db, business_id),

        "forecast_vibe": await AnalyticsService.forecast_vibe_score(db, business_id),
        # CHART DATA (VibeChart)
        "vibe_chart": {
            "7D": vibe_score_daily["data"],
            "30D": vibe_score_weekly["data"],
            "90D": vibe_score_monthly["data"],
        },
  
        # ASPECTS (AspectAnalytics)
        "aspects": [
            {
                "name": k,
                "score": v["avg_score"],
                "label": v["label"],

                # NEW: include time-series trend
                "trend": aspects["trends"].get(k, {}).get("trend", "stable"),
                "timeline": aspects["trends"].get(k, {}).get("data", []),
            }
            for k, v in aspects["summary"].items()
        ],
        "latest_reviews": await review_service.get_latest_reviews_for_business(db, business_id, limit=5)
    }


@router.get("/analytics")
async def get_analytics(
    business_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(auth_service.get_authenticated_user),
):
    
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

    return {

        "profile": await business_service.get_business_profile(db, business_id),

        "vibe_trend": await AnalyticsService.get_vibe_score_trend(db, business_id),
        "vibe_volatility": await AnalyticsService.get_vibe_volatility(db, business_id),

        # optional fallback snapshot summary
        "vibe_history": await business_service.get_business_vibe_snapshots(db, business_id),
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

        "spike_analysis": await AnalyticsService.get_review_event_detection(db, business_id)
    }


# -------------------------
# GET SINGLE BUSINESS (GENERIC - MUST COME LAST)
# -------------------------
@router.get("/{business_id}", response_model=BusinessResponse)
async def get_business(
    business_id: int, db: Annotated[AsyncSession, Depends(get_db)]
) -> Business:
    business = await business_service.get_business_or_404(db, business_id)
    return business


# -------------------------
# UPDATE BUSINESS
# -------------------------
@router.patch("/{business_id}", response_model=BusinessResponse)
async def update_business(
    business_id: int,
    updated_business: BusinessUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Business:
    return await business_service.update_business(db, business_id, updated_business)


# -------------------------
# DELETE BUSINESS
# -------------------------
@router.delete("/{business_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_business(
    business_id: int, db: Annotated[AsyncSession, Depends(get_db)]
):
    await business_service.delete_business(db, business_id)

