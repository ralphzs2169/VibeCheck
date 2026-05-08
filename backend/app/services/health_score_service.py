import numpy as np

# -------------------------
# DATA UTILITIES
# -------------------------

def get_data_quality(review_count: int):
    if review_count == 0:
        return "no_data"
    elif review_count < 3:
        return "very_low"
    elif review_count < 10:
        return "low"
    elif review_count < 50:
        return "moderate"
    return "high"


def compute_confidence(review_count: int, cfg):
    k = max(1e-6, cfg["confidence"]["half_saturation_reviews"])

    confidence = review_count / (review_count + k)

    return max(0.0, min(1.0, confidence))


def compute_aspect_stability(values, cfg):
    min_aspects = cfg["aspects"]["min_aspects"]

    if len(values) < min_aspects:
        return {"consistency": cfg["aspects"]["default_consistency"]}

    norm_vals = [(v + 1) / 2 for v in values]
    spread = np.std(norm_vals)

    sens = max(0.1, min(cfg["aspects"]["stability_sensitivity"], 10))

    stability = 1 / (1 + sens * spread)

    # small sample penalty
    penalty = len(values) / min_aspects
    penalty = max(0.2, min(1.0, penalty))

    consistency = stability * penalty

    return {
        "consistency": max(0.0, min(1.0, consistency))
    }


# -------------------------
# NORMALIZATION HELPERS
# -------------------------

def normalize_vibe_score(vibe_score: float) -> float:
    """
    Normalizes vibe score from a 1–5 scale into 0–1 range.
    """
    if vibe_score is None:
        return 0.0

    normalized = (vibe_score - 1) / 4
    return max(0.0, min(1.0, normalized))


def normalize_trend(trend: str, config: dict) -> float:
    """
    Converts trend label into normalized score (0–1).
    """
    if not trend:
        return 0.5  # neutral fallback

    trend_map = config["trend"]["mapping"]
    trend_raw = trend_map.get(trend, 0)

    normalized = (trend_raw + 1) / 2
    return max(0.0, min(1.0, normalized))


# ------------------------- 
# SCORING ENGINE
# -------------------------

def compute_final_score(
    vibe: float,
    trend: float,
    consistency: float,
    confidence: float,
    is_cold_start: bool,
    data_quality: str,
    config: dict
) -> float:
    """
    Computes final business health score (0–1) using weighted signals.
    """

    weights = (
        config["cold_start_weights"]
        if is_cold_start
        else config["weights"]
    )

    dq_factor = config["data_quality_weights"].get(data_quality, 1.0)

    if is_cold_start:
        score = (
            vibe * weights["vibe"] +
            consistency * weights["consistency"]
        )
    else:
        score = (
            vibe * weights["vibe"] +
            trend * weights["trend"] +
            consistency * weights["consistency"] +
            confidence * weights["confidence"]
        )

    score *= dq_factor

    return max(0.0, min(1.0, score))


# --------------------------
# BUSINESS HEALTH MAPPERS
# --------------------------

def get_no_data_business_health():
    return {
        "status": "no_data",
        "score": None,
        "raw": {
            "vibe_score": None,
            "trend_label": "no_data",
            "review_count": 0,
            "data_quality": "no_data",
            "is_cold_start": True
        },
        "label": "No data",
        "breakdown": {
            "vibe": None,
            "trend": None,
            "consistency": None,
            "confidence": 0.0
        },
        "insights": {
            "consistency": {
                "label": "Insufficient data",
                "meaning": "No reviews available yet",
                "level": "neutral"
            },
            "confidence": {
                "label": "No confidence",
                "meaning": "No customer data available",
                "level": "neutral"
            },
            "health": {
                "label": "No data",
                "level": "neutral",
                "meaning": "Business health cannot be assessed yet"
            }
        }
    }


def build_health_response(
    score: float,
    raw_vibe: float,
    trend: str,
    review_count: int,
    data_quality: str,
    is_cold_start: bool,
    vibe_norm: float,
    trend_norm: float,
    consistency: float,
    confidence: float,
    health_label: dict,
    consistency_label: dict,
    confidence_label: dict
):
    """
    Builds final API response payload for business health.
    """

    return {
        "status": "computed",
        "score": float(score),

        "raw": {
            "vibe_score": raw_vibe,
            "trend_label": trend,
            "review_count": review_count,
            "data_quality": data_quality,
            "is_cold_start": is_cold_start
        },

        "label": health_label["label"],

        "breakdown": {
            "vibe": float(vibe_norm),
            "trend": float(trend_norm),
            "consistency": float(consistency),
            "confidence": float(confidence)
        },

        "insights": {
            "consistency": consistency_label,
            "confidence": confidence_label,
            "health": health_label
        }
    }


# --------------------------
# LABEL MAPPERS
# --------------------------

def map_consistency(consistency: float, review_count: int):
    """
    Converts aspect consistency score into a user-friendly label and meaning.
    Consistency is a measure of how aligned customer opinions are across different aspects.
    """

    # For very low review counts, we cannot reliably assess consistency, so we return a special label.
    if 1 <= review_count < 3:
        return {
            "label": "Insufficient data",
            "meaning": "Not enough reviews to evaluate consistency",
            "level": "neutral"
        }
    
    # Clamp consistency to [0, 1] range
    consistency = max(0, min(1, consistency))

    if consistency >= 0.8:
        return {
            "label": "Highly consistent",
            "meaning": "Customers agree strongly across all aspects",
            "level": "excellent"
        }

    elif consistency >= 0.6:
        return {
            "label": "Consistent",
            "meaning": "Customer opinions are mostly aligned",
            "level": "good"
        }

    elif consistency >= 0.4:
        return {
            "label": "Mixed feedback",
            "meaning": "Some differences across customer experiences",
            "level": "moderate"
        }

    elif consistency >= 0.2:
        return {
            "label": "Inconsistent",
            "meaning": "Customer experiences vary significantly",
            "level": "poor"
        }

    else:
        return {
            "label": "Highly inconsistent",
            "meaning": "Strong disagreement in customer feedback",
            "level": "critical"
        }


def map_confidence(confidence: float, review_count: int):
    """
    Converts confidence score into a user-friendly label and meaning.
    Confidence reflects the reliability of the business health assessment 
    based on the number of reviews.
    """
    if 1 <= review_count < 3:
        return {
            "label": "Very early data",
            "meaning": "Too few reviews for reliable conclusions",
            "level": "weak"
        }

    # Clamp confidence to [0, 1] range
    confidence = max(0, min(1, confidence))

    if confidence >= 0.8:
        return {
            "label": "High confidence",
            "meaning": "Strong data backing this insight",
            "level": "reliable"
        }

    elif confidence >= 0.6:
        return {
            "label": "Good confidence",
            "meaning": "Sufficient data for reliable insights",
            "level": "good"
        }

    elif confidence >= 0.4:
        return {
            "label": "Moderate confidence",
            "meaning": "Some uncertainty due to limited data",
            "level": "moderate"
        }

    elif confidence >= 0.2:
        return {
            "label": "Low confidence",
            "meaning": "Not enough reviews for strong conclusions",
            "level": "weak"
        }

    else:
        return {
            "label": "Very low confidence",
            "meaning": "Insights may be unreliable due to very small dataset",
            "level": "critical"
        }
    

def map_business_health_label(score: float):
    """
    Converts normalized business health score (0–1) into a user-friendly label.
    """

    score = max(0, min(1, score))

    if score >= 0.75:
        return {
            "label": "Excellent",
            "level": "excellent",
            "meaning": "Business is performing very well across all signals"
        }

    elif score >= 0.55:
        return {
            "label": "Healthy",
            "level": "good",
            "meaning": "Business performance is solid and stable"
        }

    elif score >= 0.35:
        return {
            "label": "Fair",
            "level": "moderate",
            "meaning": "Business is performing average with some weak signals"
        }

    elif score >= 0.15:
        return {
            "label": "Weak",
            "level": "poor",
            "meaning": "Business shows multiple negative indicators"
        }

    else:
        return {
            "label": "Critical",
            "level": "critical",
            "meaning": "Business shows severe negative signals"
        }