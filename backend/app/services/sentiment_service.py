# from transformers import pipeline

# sentiment_pipeline = pipeline(
#     "text-classification",
#     model="cardiffnlp/twitter-xlm-roberta-base-sentiment"
# )

# def analyze_sentiment(text: str):
#     result = sentiment_pipeline(text)[0]

#     label_map = {
#         "LABEL_0": "negative",
#         "LABEL_1": "neutral",
#         "LABEL_2": "positive",
#     }

#     sentiment_label = label_map[result["label"]]
#     sentiment_score = result["score"]

#     return sentiment_score, sentiment_label