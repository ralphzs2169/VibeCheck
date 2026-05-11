from datetime import UTC, datetime

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from backend.app.core.database import get_db
from backend.app.core.dependencies import get_models
from backend.app.routers import businesses
from backend.app.services.auth_service import get_authenticated_user


def _business_response(business_id: int = 1) -> dict:
	now = datetime.now(UTC).isoformat()
	return {
		"id": business_id,
		"name": "Route Bistro",
		"location": "Cebu",
		"short_description": "Route test business",
		"image_path": None,
		"created_at": now,
		"updated_at": now,
		"latest_vibe": None,
		"reviews": [],
	}


@pytest_asyncio.fixture
async def client():
	app = FastAPI()
	app.include_router(businesses.router, prefix="/api/businesses")

	async def _fake_db():
		yield object()

	def _fake_models():
		return object()

	def _fake_current_user():
		return type("User", (), {"id": 3})()

	app.dependency_overrides[get_db] = _fake_db
	app.dependency_overrides[get_models] = _fake_models
	app.dependency_overrides[get_authenticated_user] = _fake_current_user

	transport = ASGITransport(app=app)
	async with AsyncClient(transport=transport, base_url="http://test") as ac:
		yield ac


@pytest.mark.asyncio
async def test_create_business_route_returns_201(client, monkeypatch):
	async def _create_business(_db, payload):
		assert payload.name == "New Place"
		return type("Business", (), {"id": 11})()

	async def _get_profile(_db, business_id):
		assert business_id == 11
		return _business_response(11)

	monkeypatch.setattr(businesses.business_service, "create_business", _create_business)
	monkeypatch.setattr(businesses.business_service, "get_business_profile", _get_profile)

	response = await client.post(
		"/api/businesses",
		json={
			"name": "New Place",
			"location": "Manila",
			"short_description": "Good food",
			"image_path": None,
		},
	)

	assert response.status_code == 201
	assert response.json()["id"] == 11


@pytest.mark.asyncio
async def test_get_businesses_route_include_vibe_true(client, monkeypatch):
	async def _with_vibe(_db):
		return [{"id": 1, "name": "A"}, {"id": 2, "name": "B"}]

	monkeypatch.setattr(
		businesses.business_service,
		"get_all_businesses_with_latest_vibe",
		_with_vibe,
		raising=False,
	)

	response = await client.get("/api/businesses?include_vibe=true")

	assert response.status_code == 200
	body = response.json()
	assert len(body) == 2
	assert body[0]["name"] == "A"


@pytest.mark.asyncio
async def test_get_businesses_route_include_vibe_false(client, monkeypatch):
	async def _without_vibe(_db):
		return [_business_response(21), _business_response(22)]

	monkeypatch.setattr(businesses.business_service, "get_all_businesses", _without_vibe)

	response = await client.get("/api/businesses?include_vibe=false")

	assert response.status_code == 200
	body = response.json()
	assert len(body) == 2
	assert body[1]["id"] == 22


@pytest.mark.asyncio
async def test_update_current_business_profile_route(client, monkeypatch):
	captured = {"business_id": None, "name": None}

	def _resolve_business_id(_user, _business_id):
		return 44

	async def _update_business(_db, business_id, payload):
		captured["business_id"] = business_id
		captured["name"] = payload.name

	async def _get_profile(_db, business_id):
		return {
			**_business_response(business_id),
			"name": captured["name"] or "Route Bistro",
		}

	monkeypatch.setattr(businesses.business_service, "resolve_user_business_id", _resolve_business_id)
	monkeypatch.setattr(businesses.business_service, "update_business", _update_business)
	monkeypatch.setattr(businesses.business_service, "get_business_profile", _get_profile)

	response = await client.patch(
		"/api/businesses/profile",
		data={"name": "Updated Bistro", "location": "Cebu"},
	)

	assert response.status_code == 200
	assert captured["business_id"] == 44
	assert response.json()["name"] == "Updated Bistro"
