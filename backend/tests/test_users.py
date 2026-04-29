import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from backend.app.main import app
from backend.app.core.database import get_db, Base
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

TestingSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


# Override the get_db dependency to use the test database
async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db


# setup and teardown the database for tests
@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


# Create an async test client for the FastAPI app
@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# Test cases for User endpoints
@pytest.mark.asyncio
async def test_create_user(client):
    response = await client.post("/api/users", json={
        "username": "john",
        "firstname": "John",
        "lastname": "Doe"
    })

    assert response.status_code == 201
    assert response.json()["username"] == "john"


@pytest.mark.asyncio
async def test_create_duplicate_user(client):
    await client.post("/api/users", json={
        "username": "dup",
        "firstname": "A",
        "lastname": "B"
    })

    response = await client.post("/api/users", json={
        "username": "dup",
        "firstname": "X",
        "lastname": "Y"
    })

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_get_user_success(client):
    create = await client.post("/api/users", json={
        "username": "alice",
        "firstname": "Alice",
        "lastname": "Smith"
    })

    user_id = create.json()["id"]

    response = await client.get(f"/api/users/{user_id}")

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_update_user(client):
    create = await client.post("/api/users", json={
        "username": "bob",
        "firstname": "Bob",
        "lastname": "Marley"
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
        "lastname": "User"
    })

    user_id = create.json()["id"]

    response = await client.delete(f"/api/users/{user_id}")

    assert response.status_code == 204