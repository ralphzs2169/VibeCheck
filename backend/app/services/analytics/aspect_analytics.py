from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.constants import (
    ABSA_NEGATIVE_THRESHOLD,
    ABSA_POSITIVE_THRESHOLD,
    MIN_ASPECT_COUNT,
)
from backend.app.core.aspects import ASPECTS
from backend.app.models.aspect_sentiment import AspectSentiment
from backend.app.models.review import Review

from backend.app.services.analytics.helpers import reliability

async def get_business_aspect_summary(
        db: AsyncSession,
        business_id: int
    ):
    """
    Provides aspect-level sentiment analysis summary for a business, including average sentiment score,
    review count, and a label (positive/negative/neutral) for each aspect. Also includes trend data to show
    sentiment trends over time.
    """

    # Aggregate aspect sentiment scores and counts grouped by aspect and month
    stmt = (
        select(
            AspectSentiment.aspect,
            func.strftime("%Y-%m", Review.created_at).label("period"),
            func.avg(AspectSentiment.sentiment_score).label("avg_score"),
            func.count(AspectSentiment.id).label("count"),
        )
        .join(Review, AspectSentiment.review_id == Review.id)
        .where(Review.business_id == business_id)
        .group_by(
            AspectSentiment.aspect,
            func.strftime("%Y-%m", Review.created_at)
        )
        .order_by(AspectSentiment.aspect, "period")
    )

    result = await db.execute(stmt)
    rows = result.all()

    if not rows:
        return {
            "summary": {},
            "trends": {},
            "meta": reliability(0, MIN_ASPECT_COUNT)
        }

    summary = {}
    trends = {}

    total_aspects = 0

    # Calculate weighted average sentiment score for each aspect and prepare trend data
    for row in rows:
        aspect = row.aspect
        avg = float(row.avg_score)
        count = int(row.count)
        period = row.period

        total_aspects += count

        #  
        if aspect not in summary:
            summary[aspect] = {
                "total_score": 0.0,
                "total_count": 0
            }

        summary[aspect]["total_score"] += avg * count
        summary[aspect]["total_count"] += count

        # Prepare data for trend analysis
        if aspect not in trends:
            trends[aspect] = []

        trends[aspect].append({
            "period": period,
            "avg_score": avg,
            "count": count
        })

    # -----------------------------
    # finalize summary + compute trends
    # -----------------------------
    final_summary = {}
    final_trends = {}

    for aspect, data in summary.items():
        avg = data["total_score"] / data["total_count"]

        # -------------------------
        # SUMMARY LABEL
        # -------------------------
        label = (
            "positive" if avg > ABSA_POSITIVE_THRESHOLD
            else "negative" if avg < ABSA_NEGATIVE_THRESHOLD
            else "neutral"
        )

        final_summary[aspect] = {
            "avg_score": avg,
            "count": data["total_count"],
            "label": label
        }

    # -----------------------------
    # TREND CLASSIFICATION
    # -----------------------------
    def compute_trend(points):
        if len(points) < 2:
            return "stable"

        points = sorted(points, key=lambda x: x["period"])

        first = points[0]["avg_score"]
        last = points[-1]["avg_score"]

        delta = last - first

        if delta > 0.05:
            return "improving"
        elif delta < -0.05:
            return "declining"
        return "stable"

    for aspect, points in trends.items():
        final_trends[aspect] = {
            "data": points,
            "trend": compute_trend(points)
        }

    # -----------------------------
    # return
    # -----------------------------
    return {
        "summary": final_summary,
        "trends": final_trends,
        "meta": reliability(total_aspects, MIN_ASPECT_COUNT)
    }


async def get_frequent_aspect_mining(
        db: AsyncSession,
        business_id: int,
        aspects: dict,
    ):
        """
        Builds a frequent aspect mining payload using the existing aspect summary.

        Returns all known aspects, including zero-count aspects, so the UI can
        show a complete sample distribution.
        """

        aspect_summary = aspects.get("summary", {}) if isinstance(aspects, dict) else {}

        total_mentions = sum(item.get("count", 0) for item in aspect_summary.values())

        frequent_aspects = [
            {
                "term": aspect,
                "count": int(aspect_summary.get(aspect, {}).get("count", 0)),
            }
            for aspect in ASPECTS.keys()
        ]

        return {
            "status": "computed" if aspect_summary else "no_data",
            "aspects": frequent_aspects,
            "meta": reliability(
                sample_size=total_mentions,
                minimum=1
            ),
        }
