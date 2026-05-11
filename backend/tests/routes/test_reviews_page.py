from datetime import UTC, datetime

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from backend.app.core.database import get_db
from backend.app.core.dependencies import get_models
from backend.app.routers import reviews_page
from backend.app.services.auth_service import get_authenticated_user


@pytest_asyncio.fixture
async def client():
    app = FastAPI()
    app.include_router(reviews_page.router, prefix="/api/business/reviews")

    async def _fake_db():
        yield object()

    def _fake_models():
        return object()

    def _fake_current_user():
        return type("User", (), {"id": 5})()

    app.dependency_overrides[get_db] = _fake_db
    app.dependency_overrides[get_models] = _fake_models
    app.dependency_overrides[get_authenticated_user] = _fake_current_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_get_reviews_page_returns_reviews_and_keywords(client, monkeypatch):
    now = datetime.now(UTC).isoformat()

    monkeypatch.setattr(reviews_page.business_service, "resolve_user_business_id", lambda _user, _business_id: 42)

    async def _verify_business_ownership(*_args, **_kwargs):
        return None

    monkeypatch.setattr(reviews_page.business_service, "verify_business_ownership", _verify_business_ownership)

    async def _get_reviews_for_business(_db, business_id):
        assert business_id == 42
        return [
            {
                "id": 1,
                "content": "Great service",
                "sentiment_score": 0.9,
                "sentiment_label": "positive",
                "created_at": now,
                "updated_at": now,
                "user_id": 1,
                "business_id": 42,
                "user": {
                    "id": 1,
                    "username": "reviewer01",
                    "firstname": "Rev",
                    "lastname": "User",
                    "role": "reviewer",
                    "business_id": None,
                },
                "aspect_sentiments": [],
            }
        ]

    async def _compute_vibe_keywords(_db, business_id, models, as_of_date=None, allow_insufficient_data=False):
        assert business_id == 42
        assert allow_insufficient_data is True
        return {
            "positive_keywords": ["service", "food"],
            "negative_keywords": ["wait time"],
        }

    monkeypatch.setattr(reviews_page.review_service, "get_reviews_for_business", _get_reviews_for_business)
    monkeypatch.setattr(reviews_page, "compute_vibe_keywords", _compute_vibe_keywords)

    response = await client.get("/api/business/reviews")

    assert response.status_code == 200
    body = response.json()
    assert body["business_id"] == 42
    assert body["review_count"] == 1
    assert len(body["reviews"]) == 1
    assert body["positive_keywords"] == ["service", "food"]
    assert body["negative_keywords"] == ["wait time"]
