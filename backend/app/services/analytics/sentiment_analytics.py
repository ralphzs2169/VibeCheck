# This module contains functions to compute sentiment analytics for a business based on its reviews.
# It includes functions to compute sentiment trends over time, distribution of sentiment labels, and volatility of sentiment scores. 
# Each function retrieves relevant review data from the database, performs calculations, and returns results 
import numpy as np
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.constants import (
    MIN_SENTIMENT_DISTRIBUTION_REVIEWS,
    MIN_SENTIMENT_TIMESERIES_POINTS,
    MIN_SENTIMENT_TREND_POINTS,
    MIN_SENTIMENT_VOLATILITY_POINTS,
    SENTIMENT_TREND_NEGATIVE_THRESHOLD,
    SENTIMENT_TREND_POSITIVE_THRESHOLD
)

from backend.app.models.review import Review
from backend.app.services.mapper_service import map_stability
from backend.app.services.analytics.helpers import reliability

async def get_sentiment_over_time(
    db: AsyncSession,
    business_id: int,
    granularity: str
):
    """
    Aggregates average sentiment score and review count over time for a business,
    grouped by the specified granularity (daily, weekly, monthly). This provides    
    """
    if granularity == "daily":
        bucket = func.date(Review.created_at)

    elif granularity == "weekly":
        bucket = func.strftime("%Y-%W", Review.created_at)

    elif granularity == "monthly":
        bucket = func.strftime("%Y-%m", Review.created_at)

    else:
        raise ValueError("Invalid granularity")

    # Aggregate average sentiment score and count of reviews in each time bucket
    stmt = (
        select(
            bucket.label("period"),
            func.avg(Review.sentiment_score).label("avg_score"),
            func.count(Review.id).label("count"),
        )
        .where(Review.business_id == business_id)
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
                "review_count_per_period": row.count, # count of reviews in each period
            }
            for row in rows
        ],
        "meta": reliability(len(rows), MIN_SENTIMENT_TIMESERIES_POINTS)
    }


async def get_sentiment_distribution(db: AsyncSession, business_id: int):
    """
    Calculates the distribution of sentiment labels for a given business.
    Returns the count and percentage of positive, negative, and neutral reviews, along with a reliability meta.
    """

    # Aggregate count of reviews by sentiment label
    stmt = (
        select(
            Review.sentiment_label,
            func.count(Review.id).label("count")
        )
        .where(Review.business_id == business_id)
        .group_by(Review.sentiment_label)
    )

    result = await db.execute(stmt)

    counts = {"positive": 0, "negative": 0, "neutral": 0}

    total_reviews = 0

    # Calculate total reviews and counts for each sentiment label
    for row in result:
        label = row.sentiment_label or "neutral"
        counts[label] = counts.get(label, 0) + row.count
        total_reviews += row.count

    distribution_with_percentage = {}

    # Calculate percentage for each sentiment label 
    for label, count in counts.items():
        pct = (count / total_reviews * 100) if total_reviews > 0 else 0

        distribution_with_percentage[label] = {
            "count": count,
            "percentage": round(pct, 2)
        }

    return {
        "distribution": distribution_with_percentage,
        "total_reviews": total_reviews,
        "meta": reliability(total_reviews, MIN_SENTIMENT_DISTRIBUTION_REVIEWS)
    }


async def get_sentiment_trend_slope(db: AsyncSession, business_id: int):
    """
    Calculates the trend slope of sentiment scores over time. 
    Returns the trend classification (improving/declining/stable) along with the slope value.
    """
    # Calculate average sentiment score per day
    stmt = (
        select(
            func.date(Review.created_at).label("date"),
            func.avg(Review.sentiment_score).label("avg_score")
        )
        .where(Review.business_id == business_id)
        .group_by(func.date(Review.created_at))
        .order_by(func.date(Review.created_at))
    )

    result = await db.execute(stmt)
    rows = result.all()

    # Reliability check (prevents noisy / invalid regression)
    is_reliable = len(rows) >= MIN_SENTIMENT_TREND_POINTS

    if not is_reliable:
        return {
            "trend": "insufficient_data",
            "slope": 0.0,
            "meta": reliability(len(rows), MIN_SENTIMENT_TREND_POINTS)
        }

    # Prepare regression data
    x = np.arange(len(rows))
    y = np.array([r.avg_score for r in rows])

    # Linear regression slope
    slope = np.polyfit(x, y, 1)[0]

    # Interpret trend
    trend = (
        "improving" if slope > SENTIMENT_TREND_POSITIVE_THRESHOLD
        else "declining" if slope < SENTIMENT_TREND_NEGATIVE_THRESHOLD
        else "stable"
    )

    return {
        "trend": trend,
        "slope": float(slope),
        "meta": reliability(len(rows), MIN_SENTIMENT_TREND_POINTS)
    }


async def get_sentiment_volatility(db: AsyncSession, business_id: int):
    """ 
    Measures stability of sentiment using standard deviation.
    Returns raw metric + mapped interpretation.
    """

    stmt = select(Review.sentiment_score).where(
        Review.business_id == business_id
    )

    result = await db.execute(stmt)
    scores = [r[0] for r in result if r[0] is not None]

    total_points = len(scores)

    # reliability guard (don't report volatility if we have very few reviews, as it would be noisy and unreliable)
    if total_points < MIN_SENTIMENT_VOLATILITY_POINTS:
        return {
            "volatility": 0.0,
            "stability": "insufficient_data",
            "interpretation": map_stability(0.0, "sentiment_volatility", 0)["message"],
            "meta": reliability(
                total_points,
                MIN_SENTIMENT_VOLATILITY_POINTS
            )
        }

    # Standard deviation of sentiment scores as volatility measure
    volatility = float(np.std(scores))

    # map raw volatility to stability label and interpretation message
    mapped = map_stability(
        volatility=volatility,
        metric="sentiment_volatility",
        data_points=total_points
    )

    return {
        "volatility": volatility,
        "stability": mapped["label"],
        "interpretation": mapped["message"],
        "meta": reliability(
            total_points,
            MIN_SENTIMENT_VOLATILITY_POINTS
        )
    }

