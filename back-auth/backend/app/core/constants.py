MINUTES_BETWEEN_SNAPSHOTS = 1 # for testing, set to 1 minute.

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

# thresholds for smart "and" splitting in ABSA to avoid over-splitting 
# short clauses that may not contain multiple aspects
AND_SPLIT_THRESHOLD_SHORT = 0.5
AND_SPLIT_THRESHOLD_LONG = 0.6
AND_SPLIT_LONG_SENTENCE_SIZE = 3

# minimum length for split parts when using smart "and" splitting to avoid creating very short fragments
MIN_SPLIT_PART_LENGTH = 4

