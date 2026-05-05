import pytest


@pytest.mark.asyncio
async def test_vibe_endpoint_returns_vibe_data(client):
    """Test that vibe endpoint returns complete vibe data structure"""
    user = await client.post("/api/users", json={
        "username": "test_user_endpoint",
        "firstname": "Test",
        "lastname": "User",
        "password": "password123"
    })
    user_id = user.json()["id"]

    # Login to get auth header
    login_res = await client.post("/api/auth/login", json={
        "username": "test_user_endpoint",
        "password": "password123"
    })
    auth_header = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

    business = await client.post("/api/businesses", json={
        "name": "Test Cafe Endpoint",
        "location": "Manila",
        "short_description": "Test",
        "image_path": None
    })
    business_id = business.json()["id"]

    # Create sufficient reviews
    reviews = ["Great", "Amazing", "Excellent", "Wonderful", "Perfect"]
    for text in reviews:
        await client.post("/api/reviews", json={
            "content": text,
            "user_id": user_id,
            "business_id": business_id
        }, headers=auth_header)

    # Get vibe data
    response = await client.get(f"/api/businesses/vibe/{business_id}")
    assert response.status_code == 200
    
    data = response.json()
    assert data.get("business_id") == business_id
    assert data.get("review_count") == len(reviews)
    assert "avg_score" in data
    assert "vibe_score" in data
    assert "vibe_label" in data
    assert "summary_text" in data
    assert "score_distribution" in data
    assert "keywords" in data
    
    # Verify score distribution
    dist = data["score_distribution"]
    assert "positive" in dist
    assert "mixed" in dist
    assert "negative" in dist
    assert "is_polarizing" in dist


@pytest.mark.asyncio
async def test_vibe_endpoint_insufficient_data(client):
    """Test vibe endpoint with insufficient reviews"""
    user = await client.post("/api/users", json={
        "username": "insufficient_user",
        "firstname": "Test",
        "lastname": "User",
        "password": "password123"
    })
    user_id = user.json()["id"]

    # Login to get auth header
    login_res = await client.post("/api/auth/login", json={
        "username": "insufficient_user",
        "password": "password123"
    })
    auth_header = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

    business = await client.post("/api/businesses", json={
        "name": "Insufficient Cafe",
        "location": "Manila",
        "short_description": "Test",
        "image_path": None
    })
    business_id = business.json()["id"]

    # Create only 1 review
    await client.post("/api/reviews", json={
        "content": "Just okay",
        "user_id": user_id,
        "business_id": business_id
    }, headers=auth_header)

    # Get vibe data
    response = await client.get(f"/api/businesses/vibe/{business_id}")
    assert response.status_code == 200
    
    data = response.json()
    assert data.get("status") == "insufficient_data"
    assert data.get("business_id") == business_id
    assert data.get("review_count") == 1


@pytest.mark.asyncio
async def test_vibe_snapshots_empty_business(client):
    """Test vibe snapshots endpoint with no reviews"""
    business = await client.post("/api/businesses", json={
        "name": "Empty Cafe",
        "location": "Manila",
        "short_description": "Test",
        "image_path": None
    })
    business_id = business.json()["id"]

    # Get snapshots for empty business
    response = await client.get(f"/api/businesses/vibe_snapshots/{business_id}")
    assert response.status_code == 200
    
    snapshots = response.json()
    assert snapshots == []


@pytest.mark.asyncio
async def test_vibe_snapshots_nonexistent_business(client):
    """Test vibe snapshots endpoint for non-existent business"""
    response = await client.get("/api/businesses/vibe_snapshots/99999")
    assert response.status_code == 404
