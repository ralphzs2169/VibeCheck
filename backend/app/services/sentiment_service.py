from transformers import pipeline

sentiment_pipeline = pipeline(
    "sentiment-analysis",
    model="distilbert-base-uncased-finetuned-sst-2-english"
)

def analyze_sentiment(text: str):
    result = sentiment_pipeline(text, truncation=True, max_length=512)[0]

    raw_label = result["label"]
    confidence = float(result["score"])

    # Normalize label to lowercase meaning
    if raw_label == "NEGATIVE":
        label = "negative"
        polarity_score = -confidence
    elif raw_label == "POSITIVE":
        label = "positive"
        polarity_score = confidence
    else:
        # fallback (just in case model changes or edge cases appear)
        label = "neutral"
        polarity_score = 0.0

    return polarity_score, label, confidence