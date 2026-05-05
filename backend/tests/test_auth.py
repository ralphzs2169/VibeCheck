import pytest


@pytest.mark.asyncio
async def test_login_flow(client):
    """Test the complete login flow: login -> get token -> use token"""
    # Step 1: Create a user first
    user_response = await client.post("/api/users", json={
        "username": "authtest",
        "firstname": "Auth",
        "lastname": "Test",
        "password": "password123"
    })
    assert user_response.status_code == 201
    user_id = user_response.json()["id"]

    # Step 2: Login with credentials
    login_response = await client.post("/api/auth/login", json={
        "username": "authtest",
        "password": "password123"
    })
    
    print(f"Login status: {login_response.status_code}")
    print(f"Login response: {login_response.json()}")
    
    assert login_response.status_code == 200
    token_data = login_response.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"
    
    access_token = token_data["access_token"]

    # Step 3: Use the token to call /me
    me_response = await client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    print(f"Me status: {me_response.status_code}")
    print(f"Me response: {me_response.json()}")
    
    assert me_response.status_code == 200
    me_data = me_response.json()
    assert me_data["id"] == user_id
    assert me_data["username"] == "authtest"


@pytest.mark.asyncio
async def test_me_without_token(client):
    """Test that /me fails without a token"""
    response = await client.get("/api/auth/me")
    
    print(f"No token status: {response.status_code}")
    print(f"No token response: {response.json()}")
    
    assert response.status_code == 401  # Unauthorized
    assert "Not authenticated" in response.json()["detail"]


@pytest.mark.asyncio
async def test_me_with_invalid_token(client):
    """Test that /me fails with an invalid token"""
    response = await client.get(
        "/api/auth/me",
        headers={"Authorization": "Bearer invalid_token_xyz"}
    )
    
    print(f"Invalid token status: {response.status_code}")
    print(f"Invalid token response: {response.json()}")
    
    assert response.status_code == 401
    assert "Invalid or expired token" in response.json()["detail"]
