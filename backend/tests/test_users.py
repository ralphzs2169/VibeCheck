import pytest

@pytest.mark.asyncio
async def test_create_user(client):
    response = await client.post("/api/users", json={
        "username": "john",
        "firstname": "John",
        "lastname": "Doe",
        "password": "Password123"
    })

    assert response.status_code == 201
    assert response.json()["username"] == "john"


@pytest.mark.asyncio
async def test_login_and_me(client):
    password = "Password123"
    response = await client.post("/api/users", json={
        "username": "auth_john",
        "firstname": "John",
        "lastname": "Auth",
        "password": password,
    })
    assert response.status_code == 201

    login_response = await client.post("/api/users/login", json={
        "username": "auth_john",
        "password": password,
    })
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    me_response = await client.get(
        "/api/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_response.status_code == 200
    assert me_response.json()["username"] == "auth_john"


@pytest.mark.asyncio
async def test_create_duplicate_user(client):
    await client.post("/api/users", json={
        "username": "dup",
        "firstname": "A",
        "lastname": "B",
        "password": "Password123"
    })

    response = await client.post("/api/users", json={
        "username": "dup",
        "firstname": "X",
        "lastname": "Y",
        "password": "Password123"
    })

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_get_user_success(client):
    create = await client.post("/api/users", json={
        "username": "alice",
        "firstname": "Alice",
        "lastname": "Smith",
        "password": "Password123"
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
        "password": "Password123"
    })

    user_id = create.json()["id"]

    response = await client.patch(f"/api/users/{user_id}", json={
        "firstname": "Robert"
    })

    assert response.status_code == 200
    assert response.json()["firstname"] == "Robert"


@pytest.mark.asyncio
async def test_delete_user(client):
    create = await client.post("/api/users", json={
        "username": "to_delete",
        "firstname": "Temp",
        "lastname": "User",
        "password": "Password123"
    })

    user_id = create.json()["id"]

    response = await client.delete(f"/api/users/{user_id}")

    assert response.status_code == 204