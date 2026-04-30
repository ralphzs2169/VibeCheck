import pytest


# 1. Insufficient data case (only 1 review)
@pytest.mark.asyncio
async def test_vibe_insufficient_data(client):
    user = await client.post("/api/users", json={
        "username": "u1",
        "firstname": "Test",
        "lastname": "User"
    })
    user_id = user.json()["id"]

    business = await client.post("/api/businesses", json={
        "name": "Low Data Cafe",
        "location": "Cebu",
        "short_description": "Test",
        "image_path": None
    })
    business_id = business.json()["id"]

    await client.post("/api/reviews", json={
        "content": "Good place",
        "user_id": user_id,
        "business_id": business_id
    })

    result = await client.get(f"/api/businesses/vibe/{business_id}")

    assert result.status_code == 200
    assert result.json()["status"] == "insufficient_data"
    assert result.json()["business_id"] == business_id


# 2. Positive case
@pytest.mark.asyncio
async def test_vibe_positive_case(client):
    user = await client.post("/api/users", json={
        "username": "u2",
        "firstname": "Test",
        "lastname": "User"
    })
    user_id = user.json()["id"]

    business = await client.post("/api/businesses", json={
        "name": "Positive Cafe",
        "location": "Manila",
        "short_description": "Test",
        "image_path": None
    })
    business_id = business.json()["id"]

    reviews = [
        "Amazing food and service",
        "Loved the experience",
        "Will come back again"
    ]

    for r in reviews:
        await client.post("/api/reviews", json={
            "content": r,
            "user_id": user_id,
            "business_id": business_id
        })

    result = await client.get(f"/api/businesses/vibe/{business_id}")
    data = result.json()

    assert result.status_code == 200
    assert data["business_id"] == business_id
    assert data["review_count"] == 3
    assert data["avg_score"] > 0
    assert data["vibe_label"] in ["Highly Positive", "Positive", "Mixed"]
    assert "summary_text" in data


# 3. Mixed case
@pytest.mark.asyncio
async def test_vibe_mixed_case(client):
    user = await client.post("/api/users", json={
        "username": "u3",
        "firstname": "Test",
        "lastname": "User"
    })
    user_id = user.json()["id"]

    business = await client.post("/api/businesses", json={
        "name": "Mixed Cafe",
        "location": "Davao",
        "short_description": "Test",
        "image_path": None
    })
    business_id = business.json()["id"]

    reviews = [
        "Okay food",
        "Average experience",
        "Could be better",
        "Not bad"
    ]

    for r in reviews:
        await client.post("/api/reviews", json={
            "content": r,
            "user_id": user_id,
            "business_id": business_id
        })

    result = await client.get(f"/api/businesses/vibe/{business_id}")
    data = result.json()

    assert result.status_code == 200
    assert data["review_count"] == 4
    assert data["vibe_label"] in ["Mixed", "Negative", "Positive"]
    assert "score_distribution" in data

    dist = data["score_distribution"]
    assert dist["positive"] >= 0
    assert dist["mixed"] >= 0
    assert dist["negative"] >= 0


# 4. Polarizing case
@pytest.mark.asyncio
async def test_vibe_polarizing_case(client):
    user = await client.post("/api/users", json={
        "username": "u4",
        "firstname": "Test",
        "lastname": "User"
    })
    user_id = user.json()["id"]

    business = await client.post("/api/businesses", json={
        "name": "Polar Cafe",
        "location": "Cebu",
        "short_description": "Test",
        "image_path": None
    })
    business_id = business.json()["id"]

    reviews = [
        "Amazing!",
        "Terrible experience",
        "Loved it",
        "Worst service ever",
        "Great place",
        "Horrible"
    ]

    for r in reviews:
        await client.post("/api/reviews", json={
            "content": r,
            "user_id": user_id,
            "business_id": business_id
        })

    result = await client.get(f"/api/businesses/vibe/{business_id}")
    data = result.json()

    assert result.status_code == 200

    dist = data["score_distribution"]

    assert dist["positive"] > 0
    assert dist["negative"] > 0
    assert isinstance(dist["is_polarizing"], bool)