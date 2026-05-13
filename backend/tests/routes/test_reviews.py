from datetime import UTC, datetime

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from backend.app.core.database import get_db
from backend.app.routers import reviews
from backend.app.services.auth_service import get_authenticated_user


def _review_response(review_id: int = 1, user_id: int = 1, business_id: int = 1) -> dict:
	now = datetime.now(UTC).isoformat()
	return {
		"id": review_id,
		"content": "Great service",
		"sentiment_score": 0.82,
		"sentiment_label": "positive",
		"created_at": now,
		"updated_at": now,
		"user_id": user_id,
		"business_id": business_id,
		"user": {
			"id": user_id,
			"username": "reviewer01",
			"firstname": "Review",
			"lastname": "User",
			"role": "reviewer",
			"business_id": None,
		},
		"aspect_sentiments": [
			{"aspect": "service", "sentiment_label": "positive"},
		],
	}


@pytest_asyncio.fixture
async def client():
	app = FastAPI()
	app.include_router(reviews.router, prefix="/api/reviews")
	app.state.models = object()

	async def _fake_db():
		yield object()

	def _fake_current_user():
		return type("User", (), {"id": 1})()

	app.dependency_overrides[get_db] = _fake_db
	app.dependency_overrides[get_authenticated_user] = _fake_current_user

	transport = ASGITransport(app=app)
	async with AsyncClient(transport=transport, base_url="http://test") as ac:
		yield ac


@pytest.mark.asyncio
async def test_create_review_route_returns_201(client, monkeypatch):
	called = {"user_id": None}

	async def _create_review(db, review, user_id, models):
		assert db is not None
		assert review.business_id == 10
		assert models is not None
		called["user_id"] = user_id
		return _review_response(review_id=5, user_id=user_id, business_id=10)

	monkeypatch.setattr(reviews.review_service, "create_review", _create_review)

	response = await client.post(
		"/api/reviews",
		json={
			"content": "Great service",
			"business_id": 10,
		},
	)

	assert response.status_code == 201
	assert response.json()["id"] == 5
	assert called["user_id"] == 1


@pytest.mark.asyncio
async def test_get_reviews_route_returns_list(client, monkeypatch):
	async def _get_all_reviews(_db):
		return [_review_response(1), _review_response(2)]

	monkeypatch.setattr(reviews.review_service, "get_all_reviews", _get_all_reviews)

	response = await client.get("/api/reviews")

	assert response.status_code == 200
	body = response.json()
	assert len(body) == 2
	assert body[1]["id"] == 2


@pytest.mark.asyncio
async def test_update_review_route_validates_owner(client, monkeypatch):
	async def _get_review_or_404(_db, _review_id):
		return type("Review", (), {"user_id": 1})()

	async def _update_review(_db, review_id, payload, models):
		assert review_id == 12
		assert payload.content == "Updated"
		return _review_response(review_id=12)

	monkeypatch.setattr(reviews.review_service, "get_review_or_404", _get_review_or_404)
	monkeypatch.setattr(reviews.review_service, "update_review", _update_review)
	monkeypatch.setattr(reviews, "validate_owner", lambda _u, _id: None)

	response = await client.patch("/api/reviews/12", json={"content": "Updated"})

	assert response.status_code == 200
	assert response.json()["content"] == "Great service"


@pytest.mark.asyncio
async def test_get_review_aspects_route_returns_items(client, monkeypatch):
	now = datetime.now(UTC).isoformat()

	async def _get_review_aspects(_db, review_id):
		assert review_id == 7
		return [
			{
				"id": 1,
				"review_id": 7,
				"sentence": "service was excellent",
				"aspect": "service",
				"sentiment_label": "positive",
				"sentiment_score": 0.95,
				"aspect_confidence": 0.9,
				"sentiment_confidence": 0.93,
				"created_at": now,
			}
		]

	monkeypatch.setattr(reviews, "get_review_aspects", _get_review_aspects)

	response = await client.get("/api/reviews/7/aspects")

	assert response.status_code == 200
	body = response.json()
	assert len(body) == 1
	assert body[0]["aspect"] == "service"

