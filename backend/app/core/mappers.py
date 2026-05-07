def map_consistency(value: float):
    value = max(0, min(1, value))

    if value >= 0.8:
        return {
            "label": "Highly consistent",
            "meaning": "Customers agree strongly across all aspects",
            "level": "excellent"
        }

    elif value >= 0.6:
        return {
            "label": "Consistent",
            "meaning": "Customer opinions are mostly aligned",
            "level": "good"
        }

    elif value >= 0.4:
        return {
            "label": "Mixed feedback",
            "meaning": "Some differences across customer experiences",
            "level": "moderate"
        }

    elif value >= 0.2:
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


def map_confidence(value: float):
    value = max(0, min(1, value))

    if value >= 0.8:
        return {
            "label": "High confidence",
            "meaning": "Strong data backing this insight",
            "level": "reliable"
        }

    elif value >= 0.6:
        return {
            "label": "Good confidence",
            "meaning": "Sufficient data for reliable insights",
            "level": "good"
        }

    elif value >= 0.4:
        return {
            "label": "Moderate confidence",
            "meaning": "Some uncertainty due to limited data",
            "level": "moderate"
        }

    elif value >= 0.2:
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
            "meaning": "Business performance is severely poor"
        }