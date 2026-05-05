import numpy as np
from sklearn.linear_model import LinearRegression
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.constants import (
    MIN_ASPECT_COUNT,
    MIN_SENTIMENT_DISTRIBUTION_REVIEWS,
    MIN_SENTIMENT_FORECAST_POINTS,
    MIN_SENTIMENT_TIMESERIES_POINTS,
    MIN_SENTIMENT_TREND_POINTS,
    MIN_SENTIMENT_VOLATILITY_POINTS,
    MIN_VIBE_VOLATILITY_POINTS,
    MIN_VIBE_TIMESERIES_POINTS,
    MIN_VIBE_TREND_POINTS,
    VIBE_TREND_NEGATIVE_SLOPE_THRESHOLD,
    VIBE_TREND_POSITIVE_SLOPE_THRESHOLD,
    SENTIMENT_TREND_POSITIVE_THRESHOLD,
    SENTIMENT_TREND_NEGATIVE_THRESHOLD,
    VOLATILITY_STABLE_THRESHOLD,
    MIN_PEAK_DROP_POINTS,
    ABSA_NEGATIVE_THRESHOLD,
    ABSA_POSITIVE_THRESHOLD,
    EMA_ALPHA,
    Z_SCORE_SENTIMENT_THRESHOLD,
    Z_SCORE_VOLUME_THRESHOLD,
    CONFIDENCE_SENTIMENT_WEIGHT,
    CONFIDENCE_VOLUME_WEIGHT,
    MIN_SPIKE_DATA_POINTS,
)
from backend.app.models.aspect_sentiment import AspectSentiment
from backend.app.models.review import Review
from backend.app.models.vibe_snapshot import VibeSnapshot


# Meta class for analytics reliability checks
class AnalyticsMeta:
    @staticmethod
    def reliability(sample_size: int, minimum: int):
        return {
            "is_reliable": sample_size >= minimum,
            "sample_size": sample_size,
            "min_required": minimum
        }
    

class AnalyticsService:
    
    # --------------------------
    # SENTIMENT ANALYTICS
    # --------------------------

    @staticmethod
    # sentiment aggregation over time (daily/weekly/monthly)
    async def get_sentiment_over_time(
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
            "meta": AnalyticsMeta.reliability(len(rows), MIN_SENTIMENT_TIMESERIES_POINTS)
        }

    @staticmethod
    # sentiment distribution (positive/negative/neutral counts and percentages)
    async def get_sentiment_distribution(db: AsyncSession, business_id: int):

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
            "meta": AnalyticsMeta.reliability(total_reviews, MIN_SENTIMENT_DISTRIBUTION_REVIEWS)
        }
    

    @staticmethod
    # sentiment trend (slope of sentiment scores over time)
    async def get_sentiment_trend_slope(db: AsyncSession, business_id: int):

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
                "meta": AnalyticsMeta.reliability(len(rows), MIN_SENTIMENT_TREND_POINTS)
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
            "meta": AnalyticsMeta.reliability(len(rows), MIN_SENTIMENT_TREND_POINTS)
        }
    

    @staticmethod
    async def get_sentiment_volatility(db: AsyncSession, business_id: int):

        stmt = select(Review.sentiment_score).where(
            Review.business_id == business_id
        )

        result = await db.execute(stmt)
        scores = [r[0] for r in result if r[0] is not None] # Filter out None values

        total_points = len(scores)

        # Reliability check
        if total_points < MIN_SENTIMENT_VOLATILITY_POINTS:
            return {
                "volatility": 0.0,
                "stability": "insufficient_data",
                "meta": AnalyticsMeta.reliability(total_points, MIN_SENTIMENT_VOLATILITY_POINTS)
            }

        # Standard deviation of sentiment scores as volatility measure
        volatility = float(np.std(scores))

        return {
            "volatility": volatility,
            "stability": "stable" if volatility < VOLATILITY_STABLE_THRESHOLD else "unstable",
            "meta": AnalyticsMeta.reliability(total_points, MIN_SENTIMENT_VOLATILITY_POINTS)
        }
    

    @staticmethod
    # peak and drop analysis (identify days with biggest positive and negative changes in sentiment)
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

        # Reliability check - need enough data points to identify meaningful peaks/drops
        if len(rows) < MIN_PEAK_DROP_POINTS:
            return {
                "peak": None,
                "drop": None,
                "meta": AnalyticsMeta.reliability(len(rows), MIN_PEAK_DROP_POINTS)
            }


        diffs = []

        # Compare each day’s average sentiment to the previous day to find changes
        for i in range(1, len(rows)):
            prev = rows[i - 1].avg_score or 0
            curr = rows[i].avg_score or 0

            diff = curr - prev
            diffs.append((rows[i].date, diff))

        # If somehow all values are identical
        if not diffs:
            return {
                "peak": None,
                "drop": None,
                "meta": AnalyticsMeta.reliability(len(rows), MIN_PEAK_DROP_POINTS)
            }

        # Identify the day with the biggest positive change (peak) and biggest negative change (drop)
        peak = max(diffs, key=lambda x: x[1])
        drop = min(diffs, key=lambda x: x[1])

        return {
            "peak": {
                "date": peak[0],
                "change": float(peak[1])
            },
            "drop": {
                "date": drop[0],
                "change": float(drop[1])
            },
            "meta": AnalyticsMeta.reliability(len(rows), MIN_PEAK_DROP_POINTS)
        }
    

    @staticmethod
    # sentiment forecasting (predicting future sentiment score and vibe based on historical trends)
    async def forecast_sentiment(db: AsyncSession, business_id: int):

        # Get monthly sentiment averages over time
        response = await AnalyticsService.get_sentiment_over_time(
            db,
            business_id,
            "monthly"
        )

        data = response["data"]

        # Minimum data check for reliable forecasting
        if len(data) < MIN_SENTIMENT_FORECAST_POINTS:
            return {
                "status": "insufficient_data",
                "meta": AnalyticsMeta.reliability(len(data), MIN_SENTIMENT_FORECAST_POINTS)
            }

        # Prepare regression inputs
        y = np.array([item["avg_score"] for item in data])
        x = np.arange(len(y)).reshape(-1, 1)

        # Train model
        model = LinearRegression()
        model.fit(x, y)

        # Predict next value
        next_x = np.array([[len(y)]])
        prediction = model.predict(next_x)[0]

        # Convert to label
        label = (
            "positive" if prediction > 0.3
            else "negative" if prediction < -0.3
            else "mixed"
        )

        return {
            "forecast_score": float(prediction),
            "predicted_vibe": label,
            "meta": AnalyticsMeta.reliability(len(data), MIN_SENTIMENT_FORECAST_POINTS)
        }
    

    # --------------------------
    # ABSA ANALYTICS
    # --------------------------

    @staticmethod
    async def get_business_aspect_summary(
        db: AsyncSession,
        business_id: int
    ):
        
        # Aggregate average sentiment score and count for each aspect related to the business
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

        # No aspects found for this business, return insufficient data
        if not rows:
            return {
                "summary": {},
                "meta": AnalyticsMeta.reliability(0, MIN_ASPECT_COUNT)
            }

        summary = {}
        total_aspects = 0

        # Interpret average sentiment score for each aspect and create summary with label
        for row in rows:
            avg = float(row.avg_score)
            count = int(row.count)

            total_aspects += count

            summary[row.aspect] = {
                "avg_score": avg,
                "count": count,
                "label": (
                    "positive" if avg > ABSA_POSITIVE_THRESHOLD
                    else "negative" if avg < ABSA_NEGATIVE_THRESHOLD
                    else "neutral"
                )
            }

        return {
            "summary": summary,
            "meta": AnalyticsMeta.reliability(total_aspects, MIN_ASPECT_COUNT)
        }


    # --------------------------
    # VIBE-TREND ANALYTICS
    # --------------------------

    @staticmethod
    # vibe score over time (time series of vibe scores from snapshots)
    async def get_vibe_score_over_time(db: AsyncSession, business_id: int):

        # Retrieve vibe snapshots for the business
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

        return {
            "data": [
                {
                    "period": r.snapshot_date.isoformat(),
                    "score": r.vibe_score
                }
                for r in rows
            ],
            "meta": AnalyticsMeta.reliability(len(rows), MIN_VIBE_TIMESERIES_POINTS)
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

        # Reliability check - need enough data points to identify meaningful trend
        if len(rows) < MIN_VIBE_TREND_POINTS:
            return {
                "trend": "insufficient_data",
                "slope": 0.0,
                "meta": AnalyticsMeta.reliability(
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
            "meta": AnalyticsMeta.reliability(
                len(rows),
                MIN_VIBE_TREND_POINTS
            )
        }
        

    @staticmethod
    # vibe volatility (standard deviation of vibe scores over time to measure stability of business vibe)
    async def get_vibe_volatility(db: AsyncSession, business_id: int):

        stmt = select(VibeSnapshot.vibe_score).where(
            VibeSnapshot.business_id == business_id
        )

        result = await db.execute(stmt)
        rows = result.all()

        # Extract vibe scores and filter out None values (in case some snapshots failed to compute vibe score)
        scores = [r[0] for r in rows if r[0] is not None]
        total_points = len(scores)

        # reliability guard
        if total_points < MIN_VIBE_VOLATILITY_POINTS:
            return {
                "volatility": 0.0,
                "stability": "insufficient_data",
                "meta": AnalyticsMeta.reliability(
                    total_points,
                    MIN_VIBE_VOLATILITY_POINTS
                )
            }

        # Standard deviation of vibe scores as volatility measure
        volatility = float(np.std(scores))

        return {
            "volatility": volatility,
            "stability": (
                "stable"
                if volatility < VOLATILITY_STABLE_THRESHOLD
                else "unstable"
            ),
            "meta": AnalyticsMeta.reliability(
                total_points,
                MIN_VIBE_VOLATILITY_POINTS
            )
        }

    @staticmethod
    async def get_review_event_detection(
        db: AsyncSession,
        business_id: int
    ):
        
        # Aggregate average sentiment score and review count per day for the business
        #  to create time series data for event detection
        stmt = (
            select(
                func.date(Review.created_at).label("date"),
                func.avg(Review.sentiment_score).label("avg_sentiment"),
                func.count(Review.id).label("count")
            )
            .where(Review.business_id == business_id)
            .group_by(func.date(Review.created_at))
            .order_by(func.date(Review.created_at))
        )

        result = await db.execute(stmt)
        rows = result.all()

        # Reliability check - need enough data points to perform meaningful spike detection
        if len(rows) < MIN_SPIKE_DATA_POINTS:
            return {
                "event_type": "insufficient_data",
                "confidence": 0,
                "z_scores": {
                    "sentiment_z": 0.0,
                    "volume_z": 0.0
                },
                "interpretation": "Not enough data for reliable detection.",
                "meta": AnalyticsMeta.reliability(len(rows), MIN_SPIKE_DATA_POINTS)
            }

        # Extract sentiment scores and review counts into separate arrays for analysis
        sentiment = np.array([r.avg_sentiment or 0 for r in rows])
        volume = np.array([r.count for r in rows])

        # Exponential Moving Average (EMA) smoothing to identify underlying trends
        #  and reduce noise in the time series data
        def ema(series, alpha: float):
            ema_values = [series[0]]
            for i in range(1, len(series)):
                ema_values.append(alpha * series[i] + (1 - alpha) * ema_values[-1])
            return np.array(ema_values)

        sentiment_ema = ema(sentiment, EMA_ALPHA)
        volume_ema = ema(volume, EMA_ALPHA)

        # Z-score calculation to identify significant deviations from the smoothed trend
        def z_score(current, ema_series, series):
            std = np.std(series) if np.std(series) > 0 else 1.0
            return (current - ema_series) / std

        sentiment_z = z_score(sentiment[-1], sentiment_ema[-1], sentiment)
        volume_z = z_score(volume[-1], volume_ema[-1], volume)

        # Determine if there is a significant spike in sentiment and/or volume based on z-score thresholds
        sentiment_spike = abs(sentiment_z) > Z_SCORE_SENTIMENT_THRESHOLD
        volume_spike = volume_z > Z_SCORE_VOLUME_THRESHOLD

        if sentiment_spike and volume_spike:
            event_type = "true_event"
            interpretation = (
                "Strong sentiment shift combined with increased activity suggests a viral or external event."
            )

        elif sentiment_spike:
            event_type = "sentiment_only_spike"
            interpretation = (
                "Emotional shift detected without significant change in activity."
            )

        elif volume_spike:
            event_type = "volume_only_spike"
            interpretation = (
                "Unusual activity detected without major sentiment change."
            )

        else:
            event_type = "no_anomaly"
            interpretation = "No abnormal sentiment or engagement spike detected."

        # Confidence scoring based on magnitude of z-scores, giving more weight to sentiment spikes
        #  as they are more indicative of vibe changes, but also considering volume spikes as they
        #  can amplify the impact of sentiment shifts.
        confidence_raw = (
            (abs(sentiment_z) * CONFIDENCE_SENTIMENT_WEIGHT) +
            (abs(volume_z) * CONFIDENCE_VOLUME_WEIGHT)
        )

        confidence = int(min(100, max(0, confidence_raw)))

        return {
            "event_type": event_type,
            "confidence": confidence,
            "z_scores": {
                "sentiment_z": float(sentiment_z),
                "volume_z": float(volume_z)
            },
            "baseline": {
                "sentiment_ema": float(sentiment_ema[-1]),
                "volume_ema": float(volume_ema[-1])
            },
            "interpretation": interpretation,
            "meta": AnalyticsMeta.reliability(len(rows), MIN_SPIKE_DATA_POINTS)
        }