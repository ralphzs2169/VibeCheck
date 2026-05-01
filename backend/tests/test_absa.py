from backend.app.services.absa_service import detect_aspects, split_sentences


def test_split_sentences_basic():
    text = "Food is great. Service is slow! Parking is bad; location is okay?"

    result = split_sentences(text)
    joined = " ".join(result).lower()

    assert "food is great" in joined
    assert "service is slow" in joined
    assert "parking is bad" in joined


def test_detect_aspects_returns_general_when_low_similarity():
    sentence = "random unrelated text"

    result = detect_aspects(sentence)

    assert result[0][0] == "general"


def test_detect_aspects_basic_output():
    sentence = "The food was amazing and delicious"

    result = detect_aspects(sentence)

    assert isinstance(result, list)
    assert len(result) >= 1


def test_detect_aspects_empty_input():
    result = detect_aspects("")

    assert result[0][0] == "general"