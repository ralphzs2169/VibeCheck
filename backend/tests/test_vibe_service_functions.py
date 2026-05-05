import pytest

from backend.app.services.vibe_service import (
    extract_keywords,
    classify_keywords,
    build_summary,
)


@pytest.mark.asyncio
async def test_extract_keywords():
    """Test keyword extraction from reviews"""
    from backend.app.main import app

    reviews = [
        "The food was amazing and delicious",
        "Service was excellent and friendly",
        "Clean rooms and comfortable beds"
    ]

    models = app.state.models
    keywords = extract_keywords(reviews, models)

    # Should extract some keywords
    assert len(keywords) > 0
    assert isinstance(keywords, list)
    assert all(isinstance(k, str) for k in keywords)


@pytest.mark.asyncio
async def test_extract_keywords_empty():
    """Test keyword extraction with no reviews"""
    keywords = extract_keywords([], None)
    assert keywords == []


@pytest.mark.asyncio
async def test_classify_keywords_positive():
    """Test classifying positive keywords"""
    from backend.app.main import app

    keywords = ["excellent", "amazing", "wonderful", "great"]
    models = app.state.models

    pos_keywords, neg_keywords = classify_keywords(keywords, models)

    # Should have some positive keywords
    assert len(pos_keywords) > 0
    assert all(isinstance(k, str) for k in pos_keywords)


@pytest.mark.asyncio
async def test_classify_keywords_negative():
    """Test classifying negative keywords"""
    from backend.app.main import app

    keywords = ["terrible", "horrible", "awful", "poor"]
    models = app.state.models

    pos_keywords, neg_keywords = classify_keywords(keywords, models)

    # Should have some negative keywords
    assert len(neg_keywords) > 0
    assert all(isinstance(k, str) for k in neg_keywords)


@pytest.mark.asyncio
async def test_classify_keywords_empty():
    """Test classifying empty keyword list"""
    from backend.app.main import app

    models = app.state.models
    pos_keywords, neg_keywords = classify_keywords([], models)

    assert pos_keywords == []
    assert neg_keywords == []


@pytest.mark.asyncio
async def test_build_summary_basic():
    """Test building a basic vibe summary"""
    summary = build_summary(
        label="Positive",
        score=0.5,
        count=5,
        positive_keywords=["great", "good"],
        negative_keywords=["bad"],
        llm_model=None,
        use_ai_summary=False
    )

    assert isinstance(summary, str)
    assert "vibe score" in summary.lower()
    assert "5 reviews" in summary
    assert "Positive" in summary or "positive" in summary


@pytest.mark.asyncio
async def test_build_summary_no_keywords():
    """Test building summary with no keywords"""
    summary = build_summary(
        label="Mixed",
        score=0.0,
        count=3,
        positive_keywords=[],
        negative_keywords=[],
        llm_model=None,
        use_ai_summary=False
    )

    assert isinstance(summary, str)
    assert "No strong themes detected" in summary


@pytest.mark.asyncio
async def test_compute_vibe_summary_via_endpoint_insufficient(client):
    """Test vibe computation via endpoint with insufficient reviews"""
    user = await client.post("/api/users", json={
        "username": "compute_test_1",
        "firstname": "Test",
        "lastname": "User",
        "password": "password123"
    })
    user_id = user.json()["id"]

    # Login to get auth header
    login_res = await client.post("/api/auth/login", json={
        "username": "compute_test_1",
        "password": "password123"
    })
    auth_header = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

    business = await client.post("/api/businesses", json={
        "name": "Compute Test Cafe 1",
        "location": "Manila",
        "short_description": "Test",
        "image_path": None
    })
    business_id = business.json()["id"]

    await client.post("/api/reviews", json={
        "content": "Okay",
        "user_id": user_id,
        "business_id": business_id
    }, headers=auth_header)

    response = await client.get(f"/api/businesses/vibe/{business_id}")
    assert response.status_code == 200
    
    result = response.json()
    assert result.get("status") == "insufficient_data"
    assert result.get("business_id") == business_id
    assert result.get("review_count") == 1


@pytest.mark.asyncio
async def test_compute_vibe_summary_via_endpoint_sufficient(client):
    """Test vibe computation via endpoint with sufficient reviews"""
    user = await client.post("/api/users", json={
        "username": "compute_test_2",
        "firstname": "Test",
        "lastname": "User",
        "password": "password123"
    })
    user_id = user.json()["id"]

    # Login to get auth header
    login_res = await client.post("/api/auth/login", json={
        "username": "compute_test_2",
        "password": "password123"
    })
    auth_header = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

    business = await client.post("/api/businesses", json={
        "name": "Compute Test Cafe 2",
        "location": "Manila",
        "short_description": "Test",
        "image_path": None
    })
    business_id = business.json()["id"]

    reviews_text = [
        "Great place with amazing food",
        "Excellent service and clean",
        "Very good experience",
        "Loved the atmosphere",
        "Highly recommended"
    ]

    for text in reviews_text:
        await client.post("/api/reviews", json={
            "content": text,
            "user_id": user_id,
            "business_id": business_id
        }, headers=auth_header)

    response = await client.get(f"/api/businesses/vibe/{business_id}")
    assert response.status_code == 200

    result = response.json()

    # Should have full vibe data
    assert "business_id" in result
    assert result.get("business_id") == business_id
    assert "avg_score" in result
    assert "vibe_score" in result
    assert "vibe_label" in result
    assert "summary_text" in result
    assert "keywords" in result
    assert "score_distribution" in result
    assert result.get("review_count") == len(reviews_text)

    # Verify types
    assert isinstance(result["avg_score"], (int, float))
    assert isinstance(result["vibe_score"], (int, float))
    assert 1.0 <= result["vibe_score"] <= 5.0
    assert isinstance(result["vibe_label"], str)
    assert isinstance(result["summary_text"], str)
    assert isinstance(result["keywords"], list)
    assert isinstance(result["score_distribution"], dict)


@pytest.mark.asyncio
async def test_compute_vibe_summary_score_distribution(client):
    """Test that score distribution is accurately computed"""
    user = await client.post("/api/users", json={
        "username": "compute_test_4",
        "firstname": "Test",
        "lastname": "User",
        "password": "password123"
    })
    user_id = user.json()["id"]

    # Login to get auth header
    login_res = await client.post("/api/auth/login", json={
        "username": "compute_test_4",
        "password": "password123"
    })
    auth_header = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

    business = await client.post("/api/businesses", json={
        "name": "Compute Test Cafe 4",
        "location": "Manila",
        "short_description": "Test",
        "image_path": None
    })
    business_id = business.json()["id"]

    # Create deliberately mixed reviews
    positive_reviews = ["Great!", "Excellent!", "Amazing!"]
    negative_reviews = ["Bad", "Terrible", "Awful"]
    neutral_reviews = ["Okay", "Average", "Fine"]

    for text in positive_reviews + negative_reviews + neutral_reviews:
        await client.post("/api/reviews", json={
            "content": text,
            "user_id": user_id,
            "business_id": business_id
        }, headers=auth_header)

    response = await client.get(f"/api/businesses/vibe/{business_id}")
    assert response.status_code == 200

    result = response.json()
    dist = result["score_distribution"]
    assert dist.get("positive") > 0
    assert dist.get("negative") > 0
    assert dist.get("mixed") >= 0
    assert isinstance(dist.get("is_polarizing"), bool)
