from datetime import datetime

from keybert import KeyBERT
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.constants import (
    MINIMUM_REVIEW_COUNT,
    POLARIZATION_MIN_RATIO,
    VIBE_LABELS,
    VIBE_NEUTRAL_HIGH,
    VIBE_NEUTRAL_LOW,
    VIBE_THRESHOLDS,
)
from backend.app.models.review import Review
from backend.app.services.sentiment_service import analyze_sentiment

# Initialize KeyBERT model once at module level
keyword_model = KeyBERT()


async def get_reviews_with_scores(
    db: AsyncSession,
    business_id: int,
    as_of_date: datetime | None = None
) -> list[tuple]:

    stmt = (
        select(Review.content, Review.sentiment_score)
        .where(Review.business_id == business_id)
    )

    if as_of_date is not None:
        stmt = stmt.where(Review.created_at <= as_of_date)

    result = await db.execute(stmt)
    return result.all()


def compute_sentiment_scores(reviews_with_scores: list[tuple]) -> tuple[float, list[float]]:
    if not reviews_with_scores:
        return 0.0, []

    scores = [score for _, score in reviews_with_scores]
    avg_score = sum(scores) / len(scores)
    return avg_score, scores


def get_vibe_label(score: float) -> str:
    if score >= VIBE_THRESHOLDS["high_positive"]:
        return VIBE_LABELS["high_positive"]
    elif score >= VIBE_THRESHOLDS["positive"]:
        return VIBE_LABELS["positive"]
    elif score >= VIBE_THRESHOLDS["neutral"]:
        return VIBE_LABELS["mixed"]
    elif score >= VIBE_THRESHOLDS["negative"]:
        return VIBE_LABELS["negative"]
    else:
        return VIBE_LABELS["high_negative"]


def extract_keywords(reviews: list[str], top_n: int = 4) -> list[str]:
    if not reviews:
        return []

    text = " ".join(reviews)
    keywords = keyword_model.extract_keywords(
        text,
        keyphrase_ngram_range=(1, 2),
        stop_words="english",
        use_mmr=True,
        diversity=0.5,
        top_n=top_n
    )
    return [keyword for keyword, score in keywords]


def classify_keywords(keywords: list[str]) -> tuple[list[str], list[str]]:
    positive_keywords = []
    negative_keywords = []

    for keyword in keywords:
        score, label, confidence = analyze_sentiment(keyword)
        if confidence < 0.75:
            continue
        if label == "positive":
            positive_keywords.append(keyword)
        else:
            negative_keywords.append(keyword)

    return positive_keywords, negative_keywords


def convert_sentiment_to_vibe_score(score: float) -> float:
    sentiment_normalized = (score + 1) / 2
    vibe_scale_0_to_4 = sentiment_normalized * 4
    vibe_score_1_to_5 = vibe_scale_0_to_4 + 1

    return round(vibe_score_1_to_5, 1)

    
def build_summary(
    label: str,
    score: float,
    count: int,
    positive_keywords: list[str],
    negative_keywords: list[str],
) -> str:
    
    vibe_score = convert_sentiment_to_vibe_score(score)

    insight_parts = []
    if positive_keywords:
        insight_parts.append(f"Guests highlight {', '.join(positive_keywords[:2])}")
    if negative_keywords:
        insight_parts.append(f"Common concerns include {', '.join(negative_keywords[:2])}")
    if not insight_parts:
        insight_parts.append("No strong themes detected")

    insight = ". ".join(p.capitalize() for p in insight_parts) + "."

    return (
        f"Community sentiment is {label.lower()} "
        f"with a vibe score of {vibe_score}/5.0 across {count} reviews. "
        f"{insight}"
    )


def is_neutral(score: float) -> bool:
    return VIBE_NEUTRAL_LOW <= score <= VIBE_NEUTRAL_HIGH


async def compute_vibe_summary(
    db: AsyncSession,
    business_id: int,
    as_of_date: datetime.datetime | None = None,
    allow_insufficient_data: bool = False
) -> dict:
    
    
    reviews_with_scores = await get_reviews_with_scores(db, business_id, as_of_date)

    # Only block if minimum review count is required AND not allowing insufficient data
    if not allow_insufficient_data and len(reviews_with_scores) < MINIMUM_REVIEW_COUNT:
        return {
            "status": "insufficient_data",
            "business_id": business_id
        }
    
    # If no reviews at all, return insufficient data even if allowing it
    if len(reviews_with_scores) == 0:
        return {
            "status": "insufficient_data",
            "business_id": business_id
        }
    
    n_reviews = len(reviews_with_scores)

    avg_score, scores = compute_sentiment_scores(reviews_with_scores)
    label = get_vibe_label(avg_score)

    reviews_text = [content for content, _ in reviews_with_scores]

    keywords = extract_keywords(reviews_text, top_n=4)
    positive_keywords, negative_keywords = classify_keywords(keywords)

    summary = build_summary(
        label,
        avg_score,
        n_reviews,
        positive_keywords,
        negative_keywords
    )

    positive_count = sum(1 for score in scores if score > VIBE_THRESHOLDS["positive"])
    negative_count = sum(1 for score in scores if score < VIBE_THRESHOLDS["negative"])

    mixed_count = sum(1 for score in scores if is_neutral(score))

    positive_ratio = positive_count / n_reviews
    negative_ratio = negative_count / n_reviews

    is_polarizing = (
        n_reviews > 0 and
        positive_ratio > POLARIZATION_MIN_RATIO and
        negative_ratio > POLARIZATION_MIN_RATIO
    )

    return {
        "business_id": business_id,
        "avg_score": round(avg_score, 4),
        "vibe_score": convert_sentiment_to_vibe_score(avg_score),
        "vibe_label": label,
        "keywords": keywords,
        "positive_keywords": positive_keywords,
        "negative_keywords": negative_keywords,
        "summary_text": summary,
        "review_count": n_reviews,
        "score_distribution": {
            "positive": positive_count,
            "mixed": mixed_count,
            "negative": negative_count,
            "is_polarizing": is_polarizing
        }
    }