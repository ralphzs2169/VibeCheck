import pytest


@pytest.mark.asyncio
async def test_get_business_latest_vibe_insufficient_data(client):
    """Test vibe endpoint returns insufficient_data status with < minimum reviews"""
    user = await client.post("/api/users", json={
        "username": "vibe_test_user_1",
        "firstname": "Test",
        "lastname": "User",
        "password": "password123"
    })
    user_id = user.json()["id"]

    # Login to get auth header
    login_res = await client.post("/api/auth/login", json={
        "username": "vibe_test_user_1",
        "password": "password123"
    })
    auth_header = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

    business = await client.post("/api/businesses", json={
        "name": "Low Review Cafe",
        "location": "Manila",
        "short_description": "Test",
        "image_path": None
    })
    business_id = business.json()["id"]

    # Create only 1 review (below minimum threshold)
    await client.post("/api/reviews", json={
        "content": "Just okay",
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
async def test_get_business_latest_vibe_sufficient_data(client):
    """Test vibe endpoint returns full vibe data with sufficient reviews"""
    user = await client.post("/api/users", json={
        "username": "vibe_test_user_2",
        "firstname": "Test",
        "lastname": "User",
        "password": "password123"
    })
    user_id = user.json()["id"]

    # Login to get auth header
    login_res = await client.post("/api/auth/login", json={
        "username": "vibe_test_user_2",
        "password": "password123"
    })
    auth_header = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

    business = await client.post("/api/businesses", json={
        "name": "Good Review Cafe",
        "location": "Manila",
        "short_description": "Test",
        "image_path": None
    })
    business_id = business.json()["id"]

    # Create sufficient reviews
    reviews = [
        "Excellent service",
        "Amazing food",
        "Great atmosphere",
        "Will come back",
        "Highly recommended"
    ]
    for text in reviews:
        await client.post("/api/reviews", json={
            "content": text,
            "user_id": user_id,
            "business_id": business_id
        }, headers=auth_header)

    response = await client.get(f"/api/businesses/vibe/{business_id}")
    assert response.status_code == 200

    result = response.json()

    # Verify all expected fields are present
    assert result.get("business_id") == business_id
    assert result.get("review_count") == len(reviews)
    assert "avg_score" in result
    assert "vibe_score" in result
    assert "vibe_label" in result
    assert "summary_text" in result
    assert "score_distribution" in result
    assert "keywords" in result
    assert "positive_keywords" in result
    assert "negative_keywords" in result

    # Verify score distribution structure
    dist = result["score_distribution"]
    assert dist.get("positive") >= 0
    assert dist.get("mixed") >= 0
    assert dist.get("negative") >= 0
    assert isinstance(dist.get("is_polarizing"), bool)

    # Verify vibe score is in valid range
    assert 1.0 <= result["vibe_score"] <= 5.0
    assert result["vibe_label"] in ["Highly Positive", "Positive", "Mixed", "Negative", "Highly Negative"]


@pytest.mark.asyncio
async def test_get_business_latest_vibe_mixed_sentiment(client):
    """Test vibe endpoint with mixed positive/negative reviews"""
    user = await client.post("/api/users", json={
        "username": "vibe_test_user_3",
        "firstname": "Test",
        "lastname": "User",
        "password": "password123"
    })
    user_id = user.json()["id"]

    # Login to get auth header
    login_res = await client.post("/api/auth/login", json={
        "username": "vibe_test_user_3",
        "password": "password123"
    })
    auth_header = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

    business = await client.post("/api/businesses", json={
        "name": "Mixed Review Cafe",
        "location": "Manila",
        "short_description": "Test",
        "image_path": None
    })
    business_id = business.json()["id"]

    # Create mixed reviews
    reviews = [
        "Great food",
        "Terrible service",
        "Good atmosphere",
        "Slow staff",
        "Nice place"
    ]
    for text in reviews:
        await client.post("/api/reviews", json={
            "content": text,
            "user_id": user_id,
            "business_id": business_id
        }, headers=auth_header)

    response = await client.get(f"/api/businesses/vibe/{business_id}")
    assert response.status_code == 200

    result = response.json()
    assert result.get("review_count") == len(reviews)
    dist = result["score_distribution"]
    assert dist.get("positive") > 0
    assert dist.get("negative") > 0


@pytest.mark.asyncio
async def test_get_business_latest_vibe_polarizing(client):
    """Test vibe endpoint identifies polarizing sentiment"""
    user = await client.post("/api/users", json={
        "username": "vibe_test_user_4",
        "firstname": "Test",
        "lastname": "User",
        "password": "password123"
    })
    user_id = user.json()["id"]

    # Login to get auth header
    login_res = await client.post("/api/auth/login", json={
        "username": "vibe_test_user_4",
        "password": "password123"
    })
    auth_header = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

    business = await client.post("/api/businesses", json={
        "name": "Polarizing Cafe",
        "location": "Manila",
        "short_description": "Test",
        "image_path": None
    })
    business_id = business.json()["id"]

    # Create deliberately polarizing reviews
    reviews = [
        "Absolutely amazing!",
        "Terrible experience",
        "Best place ever",
        "Worst service",
        "Loved it",
        "Hated it",
        "Fantastic",
        "Awful"
    ]
    for text in reviews:
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
    assert isinstance(dist.get("is_polarizing"), bool)


@pytest.mark.asyncio
async def test_vibe_snapshots_empty(client):
    """Test vibe snapshots endpoint with no reviews"""
    business = await client.post("/api/businesses", json={
        "name": "No Snapshots Cafe",
        "location": "Manila",
        "short_description": "Test",
        "image_path": None
    })
    business_id = business.json()["id"]

    response = await client.get(f"/api/businesses/vibe_snapshots/{business_id}")
    assert response.status_code == 200
    
    snapshots = response.json()
    assert snapshots == []


@pytest.mark.asyncio
async def test_vibe_snapshots_nonexistent_business(client):
    """Test vibe snapshots endpoint for non-existent business"""
    response = await client.get("/api/businesses/vibe_snapshots/99999")
    assert response.status_code == 404

