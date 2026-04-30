VIBE_THRESHOLDS = {
    "high_positive": 0.8,
    "positive": 0.3,
    "neutral": -0.3,
    "negative": -0.8,
}

VIBE_LABELS = {
    "high_positive": "Highly Positive",
    "positive": "Positive",
    "mixed": "Mixed",
    "negative": "Negative",
    "high_negative": "Highly Negative"
}

VIBE_NEUTRAL_LOW = VIBE_THRESHOLDS["negative"]
VIBE_NEUTRAL_HIGH = VIBE_THRESHOLDS["positive"]

POLARIZATION_MIN_RATIO = 0.3 # Minimum ratio of positive and negative reviews to consider a business polarizing

MINIMUM_REVIEW_COUNT = 3 # Minimum number of reviews required to compute a vibe summary

