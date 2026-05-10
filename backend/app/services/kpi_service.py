
from backend.app.services.analytics.vibe_analytics import get_vibe_score_over_time, get_vibe_score_trend
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.review import Review
from backend.app.services.analytics.helpers import reliability

async def build_vibe_score_kpi(db, business_id: int):
    history = await get_vibe_score_over_time(db, business_id, "monthly")
    trend = await get_vibe_score_trend(db, business_id)

    data = history["data"]

    if len(data) < 2:
        return {
            "status": "insufficient_data",
            "current_score": None,
            "trend": "insufficient_data",
            "change": 0,
            "timeseries": data
        }

    current = data[-1]["avg_score"]
    previous = data[-2]["avg_score"]

    change = current - previous
    change_percent = (change / previous * 100) if previous != 0 else 0

    return {
        "status": "computed",
        "current_score": current,
        "previous_score": previous,
        "change": change,
        "change_percent": change_percent,
        "trend": trend["trend"],
        "slope": trend["slope"],
        "timeseries": [
            {"period": d["period"], "value": d["avg_score"]}
            for d in data
        ]
    }




async def build_total_reviews_kpi(db: AsyncSession, business_id: int, granularity: str = "monthly"):
    """
    Builds KPI for total review volume over time.

    Tracks:
    - current total reviews
    - change vs previous period
    - growth trend
    - timeseries for visualization
    """

    stmt = (
        select(
            func.date(Review.created_at).label("period"),
            func.count(Review.id).label("total_reviews")
        )
        .where(Review.business_id == business_id)
        .group_by(func.date(Review.created_at))
        .order_by(func.date(Review.created_at))
    )

    result = await db.execute(stmt)
    rows = result.all()

    # Transform data for timeseries
    data = [
        {"period": r.period, "value": r.total_reviews}
        for r in rows
    ]

    if len(data) < 2:
        return {
            "status": "insufficient_data",
            "current_total": None,
            "previous_total": None,
            "change": 0,
            "change_percent": 0,
            "trend": "insufficient_data",
            "timeseries": data,
            "meta": reliability(len(data), 2)
        }

    current = data[-1]["value"]
    previous = data[-2]["value"]

    change = current - previous
    change_percent = (change / previous * 100) if previous != 0 else 0

    # Simple trend classification
    if change > 0:
        trend = "growing"
    elif change < 0:
        trend = "declining"
    else:
        trend = "stable"

    return {
        "status": "computed",
        "current_total": current,
        "previous_total": previous,
        "change": change,
        "change_percent": change_percent,
        "trend": trend,
        "timeseries": data,
        "meta": reliability(len(data), 2)
    }