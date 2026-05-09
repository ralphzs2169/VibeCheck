from backend.app.core.constants import STABILITY_CONFIG, VIBE_LABEL_CONFIG

def map_vibe_score(score: float) -> str:
    cfg = VIBE_LABEL_CONFIG["thresholds"]

    if score >= cfg["very_positive"]:
        return "very_positive"
    elif score >= cfg["positive"]:
        return "positive"
    elif score >= cfg["slightly_positive"]:
        return "slightly_positive"
    elif score >= cfg["mixed"]:
        return "mixed"
    elif score >= cfg["slightly_negative"]:
        return "slightly_negative"
    elif score >= cfg["negative"]:
        return "negative"
    else:
        return "very_negative"
    



def map_stability(volatility: float, metric: str, data_points: int):
    """
    Maps raw volatility values to stability labels and interpretation messages.
    """

    threshold = STABILITY_CONFIG["thresholds"].get(metric, 0.3)  # Default threshold if metric not found

    # Bands for categorizing stability levels
    bands = STABILITY_CONFIG["bands"]

    # Reliability guard for very low data points
    if data_points == 0:
        return {
            "label": "insufficient_data",
            "message": "Not enough data to assess stability."
        }

    # Determine stability level based on volatility and predefined thresholds
    if volatility < threshold * bands["stable"]:
        level = "stable"
    elif volatility < threshold * bands["mixed"]:
        level = "mixed"
    else:
        level = "unstable"

    # Interpretation messages based on metric and stability level
    if metric == "sentiment_volatility":
        messages = {
            "stable": "Customer sentiment is consistent over time.",
            "mixed": "Some fluctuations detected in customer sentiment.",
            "unstable": "Customer sentiment is highly inconsistent."
        }

    elif metric == "vibe_volatility":
        messages = {
            "stable": "Overall business experience is consistent over time.",
            "mixed": "Business experience shows moderate fluctuations.",
            "unstable": "Business experience is highly inconsistent."
        }

    else:
        messages = {
            "stable": "Stability is consistent over time.",
            "mixed": "Some fluctuations detected in the data.",
            "unstable": "High inconsistency detected in the data."
        }

    return {
        "label": level,
        "message": messages[level]
    }