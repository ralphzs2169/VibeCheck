PASSWORD_HASH_ITERATIONS = 100_000
HOURS_BETWEEN_SNAPSHOTS = 24
DEFAULT_USER_ROLE = "reviewer"

# --------------------------
# VIBE SUMMARY CONSTANTS
# --------------------------

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

VIBE_UI_MAP = {
    "high_positive": {"type": "stable", "ui_label": "Highly Positive"},
    "positive": {"type": "stable", "ui_label": "Positive"},
    "mixed": {"type": "warning", "ui_label": "Mixed"},
    "negative": {"type": "alert", "ui_label": "Negative"},
    "high_negative": {"type": "alert", "ui_label": "Highly Negative"},
}


# number of keywords to extract for vibe summaries (can be adjusted based on desired summary length and detail)
KEYWORD_EXTRACTION_TOP_N = 4

# used to determine if a business is considered "neutral" in vibe, 
# which can affect how we present the summary
VIBE_NEUTRAL_LOW = VIBE_THRESHOLDS["negative"]
VIBE_NEUTRAL_HIGH = VIBE_THRESHOLDS["positive"]

# used to identify if a business has a polarizing vibe (significant mix of positive and negative reviews)
POLARIZATION_MIN_RATIO = 0.3 

# Minimum number of reviews required to compute a vibe summary
MINIMUM_REVIEW_COUNT = 3 

# --------------------------
# ABSA CONSTANTS
# --------------------------

# used in ABSA to determine if a sentence is relevant to an aspect
SIMILARITY_THRESHOLD = 0.35 

# used in ABSA to filter out low-confidence sentiment predictions, 
# which can help improve overall aspect sentiment accuracy
MIN_SENTIMENT_CONFIDENCE = 0.65 

# minimum number of characters for a clause to be considered valid
MIN_CLAUSE_LENGTH = 8 

# thresholds for smart "and" splitting in ABSA to avoid 
#  over-splitting short clauses that may not contain multiple aspects
AND_SPLIT_THRESHOLD_SHORT = 0.5
AND_SPLIT_THRESHOLD_LONG = 0.6
AND_SPLIT_LONG_SENTENCE_SIZE = 3

# minimum length for split parts when using smart "and" splitting to avoid creating very short fragments
MIN_SPLIT_PART_LENGTH = 4


# --------------------------
# ANALYTICS CONSTANTS
# --------------------------

# Thresholds for determining overall business health and UI presentation
BUSINESS_HEALTH_CONFIG = {
    "trend": {
        "mapping": {
            "improving": 1,
            "stable": 0,
            "declining": -1,
            "insufficient_data": 0
        }
    },

    "weights": {
        "vibe": 0.4,
        "trend": 0.25,
        "consistency": 0.2,
        "confidence": 0.15
    },

    "cold_start_weights": {
        "vibe": 0.7,
        "consistency": 0.3
    },

    "aspects": {
        "min_aspects": 2,
        "default_consistency": 0.5,
        "stability_sensitivity": 2.0
    },

    "confidence": {
        "half_saturation_reviews": 10,
        "min_score": 3,
        "low_weight": 0.3,
        "mid_weight": 0.7
    },

    "data_quality_weights": {
        "no_data": 0.3,
        "very_low": 0.5,
        "low": 0.7,
        "moderate": 0.9,
        "high": 1.0
    }
}

# Sentiment Thresholds

MIN_SENTIMENT_TIMESERIES_POINTS = 5
MIN_SENTIMENT_DISTRIBUTION_REVIEWS = 5
MIN_SENTIMENT_TREND_POINTS = 5

# Sentiment trend thresholds (slope values for determining positive/negative trends)
SENTIMENT_TREND_POSITIVE_THRESHOLD = 0.01
SENTIMENT_TREND_NEGATIVE_THRESHOLD = -0.01

# Volatility thresholds
MIN_SENTIMENT_VOLATILITY_POINTS = 5
VOLATILITY_STABLE_THRESHOLD = 0.3

# Peak and drop detection thresholds
MIN_PEAK_DROP_POINTS = 5

# Vibe forecast thresholds
MIN_VIBE_FORECAST_POINTS = 6
FUTURE_FORECAST_MONTHS = 6
MIN_VIBE_SCORE = 1.0
MAX_VIBE_SCORE = 5.0

VIBE_POSITIVE_THRESHOLD = 3.5
VIBE_NEGATIVE_THRESHOLD = 2.5

# Aspect summary thresholds
MIN_ASPECT_COUNT = 5

ABSA_POSITIVE_THRESHOLD = 0.2
ABSA_NEGATIVE_THRESHOLD = -0.2

# Vibe score time series reliability threshold
MIN_VIBE_TIMESERIES_POINTS = 7

# Vibe trend thresholds
MIN_VIBE_TREND_POINTS = 7

VIBE_TREND_POSITIVE_SLOPE_THRESHOLD = 0.01
VIBE_TREND_NEGATIVE_SLOPE_THRESHOLD = -0.01

# Vibe trend score thresholds (for comparing vibe score values, not slopes)
VIBE_TREND_POSITIVE_THRESHOLD = 3.5
VIBE_TREND_NEGATIVE_THRESHOLD = 2.5

# Vibe volatility thresholds
MIN_VIBE_VOLATILITY_POINTS = 5


# --------------------------
# Review Event Detection Constants
# --------------------------

EMA_ALPHA = 0.3

Z_SCORE_SENTIMENT_THRESHOLD = 1.5
Z_SCORE_VOLUME_THRESHOLD = 1.5

CONFIDENCE_SENTIMENT_WEIGHT = 40
CONFIDENCE_VOLUME_WEIGHT = 40

MIN_SPIKE_DATA_POINTS = 3