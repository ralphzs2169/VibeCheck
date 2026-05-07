import numpy as np
from sklearn.linear_model import LinearRegression
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.constants import (
    ABSA_NEGATIVE_THRESHOLD,
    ABSA_POSITIVE_THRESHOLD,
    CONFIDENCE_SENTIMENT_WEIGHT,
    CONFIDENCE_VOLUME_WEIGHT,
    EMA_ALPHA,
    MIN_ASPECT_COUNT,
    MIN_PEAK_DROP_POINTS,
    MIN_SENTIMENT_DISTRIBUTION_REVIEWS,
    MIN_VIBE_FORECAST_POINTS,
    MIN_SENTIMENT_TIMESERIES_POINTS,
    MIN_SENTIMENT_TREND_POINTS,
    MIN_SENTIMENT_VOLATILITY_POINTS,
    MIN_SPIKE_DATA_POINTS,
    MIN_VIBE_TIMESERIES_POINTS,
    MIN_VIBE_TREND_POINTS,
    MIN_VIBE_VOLATILITY_POINTS,
    SENTIMENT_TREND_NEGATIVE_THRESHOLD,
    SENTIMENT_TREND_POSITIVE_THRESHOLD,
    VIBE_TREND_NEGATIVE_SLOPE_THRESHOLD,
    VIBE_TREND_POSITIVE_SLOPE_THRESHOLD,
    VOLATILITY_STABLE_THRESHOLD,
    Z_SCORE_SENTIMENT_THRESHOLD,
    Z_SCORE_VOLUME_THRESHOLD,
    FUTURE_FORECAST_MONTHS,
    MIN_VIBE_SCORE,
    MAX_VIBE_SCORE,
    VIBE_POSITIVE_THRESHOLD,
    VIBE_NEGATIVE_THRESHOLD
)
from backend.app.core.mappers import map_business_health_label, map_consistency, map_confidence
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

    @staticmethod
    async def compute_business_health(
        vibe_score: float,
        trend: str,
        aspects: dict,
        review_count: int
    ):
        """
        Computes business health using raw signals + UX mapping layer.
        """

        # -------------------------
        # 1. VIBE SCORE (raw + normalized)
        # -------------------------
        raw_vibe = vibe_score  # keep original (e.g. 4.3 / 5)
        vibe_norm = (vibe_score - 1) / 4
        vibe_norm = max(0, min(1, vibe_norm))

        # -------------------------
        # 2. TREND SCORE
        # -------------------------
        trend_map = {
            "improving": 1,
            "stable": 0,
            "declining": -1
        }

        trend_raw = trend_map.get(trend, 0)
        trend_norm = (trend_raw + 1) / 2

        # -------------------------
        # 3. ASPECT CONSISTENCY
        # -------------------------
        aspect_values = [
            aspect["avg_score"]
            for aspect in aspects.values()
            if isinstance(aspect, dict) and "avg_score" in aspect
        ]

        if aspect_values:
            norm_vals = [(v + 1) / 2 for v in aspect_values]
            spread = np.std(norm_vals)
            consistency = 1 / (1 + spread)
        else:
            consistency = 0.5

        consistency = max(0, min(1, consistency))

        # -------------------------
        # 4. CONFIDENCE
        # -------------------------
        confidence = min(review_count / 100, 1)

        # -------------------------
        # 5. FINAL SCORE (0–1)
        # -------------------------
        score = (
            vibe_norm * 0.4 +
            trend_norm * 0.25 +
            consistency * 0.2 +
            confidence * 0.15
        )

        score = max(0, min(1, score))

        # -------------------------
        # 6. UX MAPPING (NOW USED CORRECTLY)
        # -------------------------
        vibe_label = map_business_health_label(score)
        consistency_label = map_consistency(consistency)
        confidence_label = map_confidence(confidence)

        # -------------------------
        # RETURN
        # -------------------------
        return {
            "score": float(score),

            # raw + normalized signals (IMPORTANT for UI clarity)
            "raw": {
                "vibe_score": raw_vibe
            },

            "label": vibe_label["label"],

            "breakdown": {
                "vibe": float(vibe_norm),
                "trend": float(trend_norm),
                "consistency": float(consistency),
                "confidence": float(confidence)
            },

            # UX enrichment layer (THIS is what frontend should show in tooltips)
            "insights": {
                "consistency": consistency_label,
                "confidence": confidence_label,
                "health": vibe_label
            }
        }
        
    # --------------------------
    # SENTIMENT ANALYTICS
    # --------------------------

    @staticmethod
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
        response = await AnalyticsService.get_vibe_score_over_time(
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
                "meta": AnalyticsMeta.reliability(
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

        predicted_vibe = (
            "positive"
            if final_prediction >= VIBE_POSITIVE_THRESHOLD
            else "negative"
            if final_prediction <= VIBE_NEGATIVE_THRESHOLD
            else "mixed"
        )

        # -------------------------
        # RETURN
        # -------------------------
        return {
            "history": data,
            "forecast": forecast,
            "forecast_score": final_prediction,
            "predicted_vibe": predicted_vibe,
            "forecast_months": FUTURE_FORECAST_MONTHS,
            "meta": AnalyticsMeta.reliability(
                len(data),
                MIN_VIBE_FORECAST_POINTS
            )
        }
    

    # --------------------------
    # ABSA ANALYTICS
    # --------------------------

    @staticmethod
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
                "meta": AnalyticsMeta.reliability(0, MIN_ASPECT_COUNT)
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
            "meta": AnalyticsMeta.reliability(total_aspects, MIN_ASPECT_COUNT)
        }


    # --------------------------
    # VIBE-TREND ANALYTICS
    # --------------------------

    @staticmethod
    # vibe score over time (time series of vibe scores from snapshots)
    async def get_vibe_score_over_time(
        db: AsyncSession,
        business_id: int,
        granularity: str
    ):
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
            "meta": AnalyticsMeta.reliability(
                len(rows),
                MIN_VIBE_TIMESERIES_POINTS
            )
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
            "reviews_analyzed": row.review_count,
            "date": row.snapshot_date
        }