from __future__ import annotations

import re
from typing import List, Tuple

import numpy as np
from sentence_transformers import util
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.aspects import ASPECT_KEYWORDS, ASPECTS
from backend.app.core.constants import (
    AND_SPLIT_LONG_SENTENCE_SIZE,
    AND_SPLIT_THRESHOLD_LONG,
    AND_SPLIT_THRESHOLD_SHORT,
    MIN_CLAUSE_LENGTH,
    MIN_SENTIMENT_CONFIDENCE,
    MIN_SPLIT_PART_LENGTH,
    SIMILARITY_THRESHOLD,
)
from backend.app.core.ml_registry import MLRegistry
from backend.app.models.aspect_sentiment import AspectSentiment
from backend.app.models.review import Review
from backend.app.services.sentiment_service import analyze_sentiment


async def get_review_aspects(db: AsyncSession, review_id: int) -> List[AspectSentiment]:
    stmt = select(AspectSentiment).where(
        AspectSentiment.review_id == review_id
    )

    result = await db.execute(stmt)
    return result.scalars().all()


# Prepare aspect keys and keywords for efficient access in ABSA functions
ASPECT_KEYS = list(ASPECTS.keys())

# flatten all aspect keywords into a single set for quick lookup 
# during smart splitting and aspect detection
ALL_ASPECT_KEYWORDS = {
    keyword for keywords in ASPECT_KEYWORDS.values()
    for keyword in keywords
}


# ------------------
# ABSA Core Logic
# ------------------

# split on commas that only splits if the clause contains a verb, to avoid over-splitting
def smart_comma_split(clause: str) -> List[str]:
    parts = [p.strip() for p in clause.split(",")]

    if len(parts) <= 1:
        return [clause]

    # only split if first part has a verb (very simple heuristic)
    if any(v in clause.lower() for v in ["is", "was", "are", "were", "looks", "feels"]):
        return parts

    return [clause]


# split on "and" that only splits if multiple parts 
# contain aspect keywords, to avoid over-splitting
def smart_and_split(clause: str) -> List[str]:
    parts = re.split(r"\band\b", clause, flags=re.IGNORECASE)

    if len(parts) <= 1:
        return [clause]

    cleaned_parts = [p.strip() for p in parts if p.strip()]

    matched_parts = sum(
        1
        for part in cleaned_parts
        # check if any aspect keywords are present in the part
        if set(re.findall(r"\b\w+\b", part.lower())) & ALL_ASPECT_KEYWORDS
    )
    
    # Require at least 50–60% of split parts to contain aspect-related keywords
    # before allowing "and"-based splitting. This prevents over-splitting in
    # generic sentences where "and" is used for listing or natural phrasing.
    if len(cleaned_parts) >= AND_SPLIT_LONG_SENTENCE_SIZE:
        threshold = AND_SPLIT_THRESHOLD_LONG
    else:
        threshold = AND_SPLIT_THRESHOLD_SHORT

    # Split only if a significant proportion of segments are aspect-relevant.
    # This ensures that "and" is treated as an aspect separator only when
    # multiple meaningful opinion units are detected.
    if (matched_parts / len(cleaned_parts)) >= threshold:
      
        return [p for p in cleaned_parts if len(p) >= MIN_SPLIT_PART_LENGTH]

    return [clause]

    
def split_sentences(text: str) -> List[str]:
    text = re.sub(r"\s+", " ", text).strip()

    # 1. split into sentences first
    sentences = re.split(r"(?<=[.!?])\s+", text)

    final_clauses = []

    # 2. split each sentence into clauses
    for s in sentences:
        s = s.strip()
        if len(s) < MIN_CLAUSE_LENGTH:
            continue
        clauses = re.split(
            r"\bbut\b|\bhowever\b|\bthough\b|\balthough\b|\byet\b",
            s,
            flags=re.IGNORECASE
        )
        for c in clauses:
            c = c.strip()
            if len(c) < MIN_CLAUSE_LENGTH:
                continue
            
            # apply smart comma splitting and then smart "and" splitting to each clause
            for sub in smart_comma_split(c):
                for final_sub in smart_and_split(sub):
                    if len(final_sub) >= MIN_CLAUSE_LENGTH:
                        final_clauses.append(final_sub)

    return final_clauses


# keyword boost to increase confidence if 
# certain aspect keywords are present in the sentence
def strong_match_boost(sentence, aspect) -> bool:
    keywords = ASPECT_KEYWORDS[aspect]
    return any(k in sentence.lower() for k in keywords)


# Aspect detection function
# uses cosine similarity to match sentences to predefined aspects
def detect_aspects(sentence: str, models: MLRegistry) -> List[Tuple[str, float]]:

    if models.aspect_embeddings is None:
        raise ValueError("aspect_embeddings not initialized")

    embedding = models.embedding.encode(sentence, convert_to_tensor=True)

    aspect_similarity = util.cos_sim(embedding, models.aspect_embeddings)[0]
    aspect_similarity = aspect_similarity.cpu().numpy()

    results = []

    for i, score in enumerate(aspect_similarity):
        aspect = ASPECT_KEYS[i]

        if score < SIMILARITY_THRESHOLD:
            # if similarity is below threshold, we can still consider it if there's a strong keyword match
            continue

        if score < 0.5 and not strong_match_boost(sentence, aspect):
            # if the similarity is low and there's no strong keyword match, skip this aspect
            continue

        results.append((aspect, float(score)))

    if not results:
        return [("general", float(np.max(aspect_similarity)))]

    return results


async def run_absa_for_review(
    db: AsyncSession,
    review: Review,
    models: MLRegistry
) -> List[AspectSentiment]:

    if review.id is None:
        await db.flush()

    sentences = split_sentences(review.content)
    results: List[AspectSentiment] = []

    seen_aspects = set() 

    # For each sentence, detect relevant aspects first, then compute
    # aspect-specific sentiment for each detected aspect.
    # Each record represents an (aspect, sentence) pair with its own sentiment score.
    for sentence in sentences:

        detected_aspects = detect_aspects(sentence, models)

        for aspect, aspect_confidence in detected_aspects:

            if aspect == "general":
                continue

            if aspect in seen_aspects:
                continue
            seen_aspects.add(aspect)


            aspect_text = f"{aspect}: {sentence}"

            sentiment_score, sentiment_label, sentiment_confidence = analyze_sentiment(
                aspect_text,
                models.sentiment
            )

            if sentiment_confidence < MIN_SENTIMENT_CONFIDENCE:
                continue

            record = AspectSentiment(
                review_id=review.id,
                sentence=sentence,
                aspect=aspect,
                sentiment_label=sentiment_label,
                sentiment_score=sentiment_score,
                aspect_confidence=aspect_confidence,
                sentiment_confidence=sentiment_confidence,
            )

            db.add(record)
            results.append(record)

    await db.commit()
    return results