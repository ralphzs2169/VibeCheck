import pytest
from backend.app.services.vibe_service import (
    get_vibe_label,
    convert_sentiment_to_vibe_score,
    is_neutral,
    compute_sentiment_scores,
)


def test_get_vibe_label_high_positive():
    assert get_vibe_label(0.9) == "Highly Positive"


def test_get_vibe_label_positive():
    assert get_vibe_label(0.5) == "Positive"


def test_get_vibe_label_mixed():
    assert get_vibe_label(0.0) == "Mixed"


def test_get_vibe_label_negative():
    assert get_vibe_label(-0.5) == "Negative"


def test_convert_sentiment_to_vibe_score():
    score = convert_sentiment_to_vibe_score(1.0)
    assert 4.5 <= score <= 5.0


def test_is_neutral():
    assert is_neutral(0.0) is True
    assert is_neutral(0.9) is False


def test_compute_sentiment_scores():
    data = [("a", 1.0), ("b", -1.0), ("c", 0.0)]

    avg, scores = compute_sentiment_scores(data)

    assert len(scores) == 3
    assert avg == pytest.approx(0.0)