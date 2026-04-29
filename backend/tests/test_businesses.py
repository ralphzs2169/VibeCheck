import pytest


# Tests - BUSINESS

@pytest.mark.asyncio
async def test_create_business(client):
    response = await client.post("/api/businesses", json={
        "name": "Cafe Uno",
        "location": "Cebu City",
        "short_description": "Cozy coffee shop",
        "image_path": None
    })

    assert response.status_code == 201
    assert response.json()["name"] == "Cafe Uno"


@pytest.mark.asyncio
async def test_create_duplicate_business(client):
    await client.post("/api/businesses", json={
        "name": "Duplicate Cafe",
        "location": "Cebu",
        "short_description": "Test",
        "image_path": None
    })

    response = await client.post("/api/businesses", json={
        "name": "Duplicate Cafe",
        "location": "Cebu",
        "short_description": "Test 2",
        "image_path": None
    })

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_get_business_success(client):
    create = await client.post("/api/businesses", json={
        "name": "Resto 1",
        "location": "Manila",
        "short_description": "Good food",
        "image_path": None
    })

    business_id = create.json()["id"]

    response = await client.get(f"/api/businesses/{business_id}")

    assert response.status_code == 200
    assert response.json()["name"] == "Resto 1"


@pytest.mark.asyncio
async def test_update_business(client):
    create = await client.post("/api/businesses", json={
        "name": "Old Name",
        "location": "Davao",
        "short_description": "Old desc",
        "image_path": None
    })

    business_id = create.json()["id"]

    response = await client.patch(f"/api/businesses/{business_id}", json={
        "name": "New Name"
    })

    assert response.status_code == 200
    assert response.json()["name"] == "New Name"


@pytest.mark.asyncio
async def test_delete_business(client):
    create = await client.post("/api/businesses", json={
        "name": "To Delete",
        "location": "Iloilo",
        "short_description": "Temp",
        "image_path": None
    })

    business_id = create.json()["id"]

    response = await client.delete(f"/api/businesses/{business_id}")

    assert response.status_code == 204