from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.review import Review
from backend.app.models.aspect_sentiment import AspectSentiment
from sklearn.linear_model import LinearRegression
import numpy as np

from backend.app.models.vibe_snapshot import VibeSnapshot

class AnalyticsService:

    # --------------------------
    # SENTIMENT ANALYTICS
    # --------------------------
    @staticmethod
    async def get_temporal_aggregation(
        db: AsyncSession,
        business_id: int,
        granularity: str
    ):
        if granularity == "daily":
            bucket = func.date(Review.created_at)

        elif granularity == "weekly":
            bucket = func.strftime("%Y-%W", Review.created_at)

        elif granularity == "monthly":
            bucket = func.strftime("%Y-%m", Review.created_at)

        else:
            raise ValueError("Invalid granularity")

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

        return [
            {
                "period": row.period,
                "avg_score": float(row.avg_score),
                "count": row.count,
            }
            for row in result
        ]

    @staticmethod
    async def get_sentiment_distribution(db: AsyncSession, business_id: int):
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

        total = 0

        for row in result:
            counts[row.sentiment_label] = row.count
            total += row.count

        return {
            "distribution": counts,
            "total": total
        }
    

    @staticmethod
    async def get_sentiment_trend_slope(db: AsyncSession, business_id: int):

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

        if len(rows) < 2:
            return {"trend": "insufficient_data", "slope": 0}

        x = np.arange(len(rows))
        y = np.array([r.avg_score for r in rows])

        slope = np.polyfit(x, y, 1)[0]

        trend = (
            "improving" if slope > 0.01
            else "declining" if slope < -0.01
            else "stable"
        )

        return {
            "trend": trend,
            "slope": float(slope)
        }
    

    @staticmethod
    async def get_sentiment_volatility(db: AsyncSession, business_id: int):

        stmt = select(Review.sentiment_score).where(
            Review.business_id == business_id
        )

        result = await db.execute(stmt)
        scores = [r[0] for r in result]

        if len(scores) < 2:
            return {"volatility": 0}

        volatility = float(np.std(scores))

        return {
            "volatility": volatility,
            "stability": "stable" if volatility < 0.3 else "unstable"
        }
    


    @staticmethod
    async def get_peak_and_drop(db: AsyncSession, business_id: int):

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

        if len(rows) < 2:
            return {"peak": None, "drop": None}

        diffs = []

        for i in range(1, len(rows)):
            diff = rows[i].avg_score - rows[i - 1].avg_score
            diffs.append((rows[i].date, diff))

        peak = max(diffs, key=lambda x: x[1])
        drop = min(diffs, key=lambda x: x[1])

        return {
            "peak": {"date": peak[0], "change": peak[1]},
            "drop": {"date": drop[0], "change": drop[1]}
        }
    
    @staticmethod
    async def forecast_sentiment(db: AsyncSession, business_id: int):
        data = await AnalyticsService.get_temporal_aggregation(
            db,
            business_id,
            "monthly"
        )

        if len(data) < 2:
            return {"status": "insufficient_data"}

        y = np.array([item["avg_score"] for item in data])
        x = np.arange(len(y)).reshape(-1, 1)

        model = LinearRegression()
        model.fit(x, y)

        next_x = np.array([[len(y)]])
        prediction = model.predict(next_x)[0]

        label = (
            "positive" if prediction > 0.3
            else "negative" if prediction < -0.3
            else "mixed"
        )

        return {
            "forecast_score": float(prediction),
            "predicted_vibe": label
        }
    

    # --------------------------
    # ABSA ANALYTICS
    # --------------------------

    @staticmethod
    async def get_business_aspect_summary(
        db: AsyncSession,
        business_id: int
    ):
        stmt = (
            select(
                AspectSentiment.aspect,
                func.avg(AspectSentiment.sentiment_score).label("avg_score"),
                func.count(AspectSentiment.id).label("count"),
            )
            .join(Review, AspectSentiment.review_id == Review.id)
            .where(Review.business_id == business_id)
            .group_by(AspectSentiment.aspect)
        )

        result = await db.execute(stmt)
        rows = result.all()

        if not rows:
            return {}

        summary = {}

        for row in rows:
            avg = float(row.avg_score)

            summary[row.aspect] = {
                "avg_score": avg,
                "count": int(row.count),
                "label": (
                    "positive" if avg > 0.2
                    else "negative" if avg < -0.2
                    else "neutral"
                )
            }

        return summary


    # --------------------------
    # VIBE-TREND ANALYTICS
    # --------------------------

    @staticmethod
    async def get_vibe_score_over_time(db: AsyncSession, business_id: int):
        stmt = (
            select(
                VibeSnapshot.snapshot_date,
                VibeSnapshot.vibe_score
            )
            .where(VibeSnapshot.business_id == business_id)
            .order_by(VibeSnapshot.snapshot_date)
        )

        result = await db.execute(stmt)
        rows = result.all()

        if not rows:
            return {
                "labels": [],
                "scores": []
            }

        return {
            "labels": [r.snapshot_date.isoformat() for r in rows],
            "scores": [r.vibe_score for r in rows]
        }


    @staticmethod
    async def get_vibe_score_trend(db: AsyncSession, business_id: int):

        stmt = (
            select(VibeSnapshot.snapshot_date, VibeSnapshot.vibe_score)
            .where(VibeSnapshot.business_id == business_id)
            .order_by(VibeSnapshot.snapshot_date)
        )

        result = await db.execute(stmt)
        rows = result.all()

        if len(rows) < 2:
            return {"trend": "insufficient_data", "slope": 0}

        base_date = rows[0].snapshot_date

        x = np.array([
            (r.snapshot_date - base_date).days
            for r in rows
        ])

        y = np.array([r.vibe_score for r in rows])

        slope = np.polyfit(x, y, 1)[0]

        trend = (
            "improving" if slope > 0.01
            else "declining" if slope < -0.01
            else "stable"
        )

        return {
            "trend": trend,
            "slope": float(slope)
        }
    

    @staticmethod
    async def get_vibe_volatility(db: AsyncSession, business_id: int):

        stmt = select(VibeSnapshot.vibe_score).where(
            VibeSnapshot.business_id == business_id
        )

        result = await db.execute(stmt)
        rows = result.all()

        scores = [r[0] for r in rows if r[0] is not None]

        if len(scores) < 2:
            return {"volatility": 0}

        volatility = float(np.std(scores))

        return {
            "volatility": volatility,
            "stability": "stable" if volatility < 0.2 else "unstable"
        }


    @staticmethod
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
            "date": row.snapshot_date
        }