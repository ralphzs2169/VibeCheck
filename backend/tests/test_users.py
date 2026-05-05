import pytest

@pytest.mark.asyncio
async def test_create_user(client):
    response = await client.post("/api/users", json={
        "username": "john",
        "firstname": "John",
        "lastname": "Doe",
        "password": "password123"
    })

    assert response.status_code == 201
    assert response.json()["username"] == "john"


@pytest.mark.asyncio
async def test_create_duplicate_user(client):
    await client.post("/api/users", json={
        "username": "dup",
        "firstname": "A",
        "lastname": "B",
        "password": "password123"
    })

    response = await client.post("/api/users", json={
        "username": "dup",
        "firstname": "X",
        "lastname": "Y",
        "password": "password123"
    })

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_get_user_success(client):
    create = await client.post("/api/users", json={
        "username": "alice",
        "firstname": "Alice",
        "lastname": "Smith",
        "password": "password123"
    })

    user_id = create.json()["id"]

    response = await client.get(f"/api/users/{user_id}")

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_update_user(client):
    create = await client.post("/api/users", json={
        "username": "bob",
        "firstname": "Bob",
        "lastname": "Marley",
        "password": "password123"
    })

    user_id = create.json()["id"]

    # Login to get auth header
    login_res = await client.post("/api/auth/login", json={
        "username": "bob",
        "password": "password123"
    })
    auth_header = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

    response = await client.patch(f"/api/users/{user_id}", json={
        "firstname": "Robert"
    }, headers=auth_header)

    assert response.status_code == 200
    assert response.json()["firstname"] == "Robert"


@pytest.mark.asyncio
async def test_delete_user(client):
    create = await client.post("/api/users", json={
        "username": "to_delete",
        "firstname": "Temp",
        "lastname": "User",
        "password": "password123"
    })

    user_id = create.json()["id"]

    # Login to get auth header
    login_res = await client.post("/api/auth/login", json={
        "username": "to_delete",
        "password": "password123"
    })
    auth_header = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

    response = await client.delete(f"/api/users/{user_id}", headers=auth_header)

    assert response.status_code == 204