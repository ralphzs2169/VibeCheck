import numpy as np
from sklearn.linear_model import LinearRegression
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.constants import (
    FUTURE_FORECAST_MONTHS,
    MAX_VIBE_SCORE,
    MIN_VIBE_FORECAST_POINTS,
    MIN_VIBE_SCORE,
    MIN_VIBE_TIMESERIES_POINTS,
    MIN_VIBE_TREND_POINTS,
    MIN_VIBE_VOLATILITY_POINTS,
    VIBE_TREND_NEGATIVE_SLOPE_THRESHOLD,
    VIBE_TREND_POSITIVE_SLOPE_THRESHOLD,
)
from backend.app.models.vibe_snapshot import VibeSnapshot
from backend.app.services.analytics.helpers import reliability
from backend.app.services.mapper_service import map_stability, map_vibe_score


async def get_latest_vibe(db: AsyncSession, business_id: int):
    stmt = (
        select(VibeSnapshot)
        .where(VibeSnapshot.business_id == business_id)
        .order_by(VibeSnapshot.snapshot_date.desc())
        .limit(1)
    )

    result = await db.execute(stmt)
    row = result.scalar_one_or_none()

    if not row:
        return {"status": "no_data"}

    return {
        "vibe_score": row.vibe_score,
        "vibe_label": row.vibe_label,
        "reviews_analyzed": row.review_count,
        "date": row.snapshot_date
    }

async def get_vibe_volatility(db: AsyncSession, business_id: int):
    """
    Measures stability of vibe scores using standard deviation of historical snapshots.
    """

    stmt = select(VibeSnapshot.vibe_score).where(
        VibeSnapshot.business_id == business_id
    )

    result = await db.execute(stmt)
    rows = result.all()

    scores = [r[0] for r in rows if r[0] is not None]
    total_points = len(scores)

    # reliability guard (don't report volatility if we have very few snapshots, as it would be noisy and unreliable)
    if total_points < MIN_VIBE_VOLATILITY_POINTS:
        return {
            "volatility": 0.0,
            "stability": "insufficient_data",
            "interpretation": map_stability(0.0, "vibe_volatility", 0)["message"],
            "meta": reliability(
                total_points,
                MIN_VIBE_VOLATILITY_POINTS
            )
        }

    # Standard deviation of vibe scores as volatility measure
    volatility = float(np.std(scores))

    # map raw volatility to stability label and interpretation message
    mapped = map_stability(
        volatility=volatility,
        metric="vibe_volatility",
        data_points=total_points
    )

    return {
        "volatility": volatility,
        "stability": mapped["label"],
        "interpretation": mapped["message"],
        "meta": reliability(
            total_points,
            MIN_VIBE_VOLATILITY_POINTS
        )
    }



async def get_vibe_score_over_time(db: AsyncSession, business_id: int, granularity: str):
    """
    Aggregates average vibe score from snapshots over time for a business,
    grouped by the specified granularity (daily, weekly, monthly). This provides a time series 
    of vibe scores to analyze trends and patterns.
    """
    if granularity == "daily":
        bucket = func.date(VibeSnapshot.snapshot_date)

    elif granularity == "weekly":
        bucket = func.strftime("%Y-%W", VibeSnapshot.snapshot_date)

    elif granularity == "monthly":
        bucket = func.strftime("%Y-%m", VibeSnapshot.snapshot_date)

    else:
        raise ValueError("Invalid granularity")

    # Aggregate average vibe score and count of snapshots in each time bucket
    stmt = (
        select(
            bucket.label("period"),
            func.avg(VibeSnapshot.vibe_score).label("avg_score"),
            func.count(VibeSnapshot.id).label("snapshot_count"),
        )
        .where(VibeSnapshot.business_id == business_id)
        .group_by("period")
        .order_by("period")
    )

    result = await db.execute(stmt)
    rows = result.all()

    return {
        "data": [
            {
                "period": row.period,
                "avg_score": float(row.avg_score) if row.avg_score is not None else 0,
                "snapshot_count": row.snapshot_count,
            }
            for row in rows
        ],
        "meta": reliability(
            len(rows),
            MIN_VIBE_TIMESERIES_POINTS
        )
    }


async def get_vibe_score_trend(db: AsyncSession, business_id: int):
    """
    Calculates the trend of vibe scores over time using linear regression slope.
    Returns the trend classification (improving/declining/stable) along with the slope value
    """
    stmt = (
        select(VibeSnapshot.snapshot_date, VibeSnapshot.vibe_score)
        .where(VibeSnapshot.business_id == business_id)
        .order_by(VibeSnapshot.snapshot_date)
    )

    result = await db.execute(stmt)
    rows = result.all()

    # Reliability check - need enough data points to identify meaningful trend
    if len(rows) < MIN_VIBE_TREND_POINTS:
        return {
            "trend": "insufficient_data",
            "slope": 0.0,
            "meta": reliability(
                len(rows),
                MIN_VIBE_TREND_POINTS
            )
        }

    # Prepare data for regression - convert dates to ordinal or numeric format
    base_date = rows[0].snapshot_date

    # Convert snapshot dates to number of days since the first snapshot for regression
    x = np.array([
        (r.snapshot_date - base_date).days
        for r in rows
    ])

    # Vibe scores as the target variable
    y = np.array([r.vibe_score for r in rows])

    # Calculate slope using linear regression 
    slope = np.polyfit(x, y, 1)[0]

    # Interpret trend based on slope thresholds
    if slope > VIBE_TREND_POSITIVE_SLOPE_THRESHOLD:
        trend = "improving"
    elif slope < VIBE_TREND_NEGATIVE_SLOPE_THRESHOLD:
        trend = "declining"
    else:
        trend = "stable"

    return {
        "trend": trend,
        "slope": float(slope),
        "meta": reliability(
            len(rows),
            MIN_VIBE_TREND_POINTS
        )
    }



async def forecast_vibe_score(db: AsyncSession, business_id: int):
    """
    Forecast future vibe score using linear regression on historical monthly vibe scores.

    Returns:
    - historical vibe score trend
    - 6-month forecast
    - predicted vibe classification
    """

    # -------------------------
    # FETCH HISTORICAL DATA
    # -------------------------
    response = await get_vibe_score_over_time(
        db,
        business_id,
        "monthly"
    )

    data = response.get("data", [])

    # -------------------------
    # VALIDATION
    # -------------------------
    if len(data) < MIN_VIBE_FORECAST_POINTS:
        return {
            "status": "insufficient_data",
            "history": data,
            "forecast": [],
            "meta": reliability(
                len(data),
                MIN_VIBE_FORECAST_POINTS
            )
        }

    # -------------------------
    # PREPARE TRAINING DATA
    # -------------------------
    y = np.array([
        item["avg_score"]
        for item in data
    ])

    x = np.arange(len(y)).reshape(-1, 1)

    # -------------------------
    # TRAIN MODEL
    # -------------------------
    model = LinearRegression()
    model.fit(x, y)

    # -------------------------
    # FORECAST FUTURE MONTHS
    # -------------------------
    future_x = np.arange(
        len(y),
        len(y) + FUTURE_FORECAST_MONTHS
    ).reshape(-1, 1)

    future_y = model.predict(future_x)

    # Clamp to valid vibe score range (1-5)
    future_y = np.clip(
        future_y,
        MIN_VIBE_SCORE,
        MAX_VIBE_SCORE
    )

    # -------------------------
    # FORMAT FORECAST
    # -------------------------
    forecast = [
        {
            "period": len(y) + i,
            "predicted": float(score)
        }
        for i, score in enumerate(future_y)
    ]

    # -------------------------
    # FINAL FORECAST VALUE
    # -------------------------
    final_prediction = float(future_y[-1])

    predicted_vibe = map_vibe_score(final_prediction)

    # -------------------------
    # RETURN
    # -------------------------
    return {
        "history": data,
        "forecast": forecast,
        "forecast_score": final_prediction,
        "predicted_vibe": predicted_vibe,
        "forecast_months": FUTURE_FORECAST_MONTHS,
        "meta": reliability(
            len(data),
            MIN_VIBE_FORECAST_POINTS
        )
    }