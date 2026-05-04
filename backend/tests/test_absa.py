import pytest
from backend.app.services.absa_service import detect_aspects, split_sentences


def test_split_sentences_basic():
    text = "Food is great. Service is slow! Parking is bad; location is okay?"

    result = split_sentences(text)
    joined = " ".join(result).lower()

    assert "food is great" in joined
    assert "service is slow" in joined
    assert "parking is bad" in joined


@pytest.mark.asyncio
async def test_detect_aspects_returns_general_when_low_similarity(client):
    sentence = "random unrelated text"

    # Get models from app state which are initialized by setup_models fixture
    models = client._transport.app.state.models
    result = detect_aspects(sentence, models)

    assert result[0][0] == "general"


@pytest.mark.asyncio
async def test_detect_aspects_basic_output(client):
    sentence = "The food was amazing and delicious"

    # Get models from app state
    models = client._transport.app.state.models
    result = detect_aspects(sentence, models)

    assert isinstance(result, list)
    assert len(result) >= 1


@pytest.mark.asyncio
async def test_detect_aspects_empty_input(client):
    # Get models from app state
    models = client._transport.app.state.models
    result = detect_aspects("", models)

    assert result[0][0] == "general"