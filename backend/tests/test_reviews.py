import pytest

@pytest.mark.asyncio
async def test_create_review(client):
    # create user + business first (important for FK)
    user = await client.post("/api/users", json={
        "username": "review_user",
        "firstname": "Rev",
        "lastname": "User",
        "password": "Password123"
    })

    business = await client.post("/api/businesses", json={
        "name": "Review Cafe",
        "location": "Cebu",
        "short_description": "Test business",
        "image_path": None
    })

    response = await client.post("/api/reviews", json={
        "content": "Amazing place!",
        "user_id": user.json()["id"],
        "business_id": business.json()["id"]
    })

    assert response.status_code == 201
    assert response.json()["content"] == "Amazing place!"


@pytest.mark.asyncio
async def test_create_review_authenticated_user(client):
    password = "Password123"
    user = await client.post("/api/users", json={
        "username": "auth_review_user",
        "firstname": "Auth",
        "lastname": "Reviewer",
        "password": password,
    })
    assert user.status_code == 201

    login_response = await client.post("/api/users/login", json={
        "username": "auth_review_user",
        "password": password,
    })
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    business = await client.post("/api/businesses", json={
        "name": "Auth Cafe",
        "location": "Cebu",
        "short_description": "Test business",
        "image_path": None
    })
    assert business.status_code == 201

    response = await client.post(
        "/api/reviews",
        json={
            "content": "Authenticated review",
            "business_id": business.json()["id"],
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 201
    assert response.json()["user_id"] == user.json()["id"]


@pytest.mark.asyncio
async def test_get_review_success(client):
    user = await client.post("/api/users", json={
        "username": "getter",
        "firstname": "Get",
        "lastname": "User",
        "password": "Password123"
    })

    business = await client.post("/api/businesses", json={
        "name": "Getter Cafe",
        "location": "Manila",
        "short_description": "Test",
        "image_path": None
    })

    create = await client.post("/api/reviews", json={
        "content": "Nice vibe",
        "user_id": user.json()["id"],
        "business_id": business.json()["id"]
    })

    review_id = create.json()["id"]

    response = await client.get(f"/api/reviews/{review_id}")

    assert response.status_code == 200
    assert response.json()["content"] == "Nice vibe"


@pytest.mark.asyncio
async def test_update_review(client):
    user = await client.post("/api/users", json={
        "username": "upd_user",
        "firstname": "Upd",
        "lastname": "User",
        "password": "Password123"
    })

    business = await client.post("/api/businesses", json={
        "name": "Update Cafe",
        "location": "Davao",
        "short_description": "Test",
        "image_path": None
    })

    create = await client.post("/api/reviews", json={
        "content": "Okay lang",
        "user_id": user.json()["id"],
        "business_id": business.json()["id"]
    })

    review_id = create.json()["id"]

    response = await client.patch(f"/api/reviews/{review_id}", json={
        "content": "Super good na pala"
    })

    assert response.status_code == 200
    assert response.json()["content"] == "Super good na pala"


@pytest.mark.asyncio
async def test_delete_review(client):
    user = await client.post("/api/users", json={
        "username": "del_user",
        "firstname": "Del",
        "lastname": "User",
        "password": "Password123"
    })

    business = await client.post("/api/businesses", json={
        "name": "Delete Cafe",
        "location": "Iloilo",
        "short_description": "Test",
        "image_path": None
    })

    create = await client.post("/api/reviews", json={
        "content": "To be deleted",
        "user_id": user.json()["id"],
        "business_id": business.json()["id"]
    })

    review_id = create.json()["id"]

    response = await client.delete(f"/api/reviews/{review_id}")

    assert response.status_code == 204