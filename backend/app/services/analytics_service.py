from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.review import Review
from sklearn.linear_model import LinearRegression
import numpy as np

class AnalyticsService:

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