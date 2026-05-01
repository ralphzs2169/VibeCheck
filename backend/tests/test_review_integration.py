import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app


@pytest.mark.asyncio
async def test_create_review_updates_vibe_flow():
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:

        # 1. Create user
        user_res = await client.post("/api/users", json={
            "username": "testuser",
            "firstname": "Test",
            "lastname": "User"
        })
        assert user_res.status_code == 201
        user_id = user_res.json()["id"]

        # 2. Create business
        business_res = await client.post("/api/businesses", json={
            "name": "Integration Cafe",
            "location": "Manila",
            "short_description": "Test business",
            "image_path": None
        })
        assert business_res.status_code == 201
        business_id = business_res.json()["id"]

        # 3. Create reviews (this should trigger vibe snapshot internally)
        reviews = [
            "Amazing food and service",
            "Loved the experience",
            "Great place overall"
        ]

        review_ids = []

        for text in reviews:
            res = await client.post("/api/reviews", json={
                "content": text,
                "user_id": user_id,
                "business_id": business_id
            })
            assert res.status_code == 201
            review_ids.append(res.json()["id"])

        # 4. Check vibe snapshots were created
        snapshot_res = await client.get(
            f"/api/businesses/vibe_snapshots/{business_id}"
        )

        assert snapshot_res.status_code == 200
        snapshots = snapshot_res.json()
        assert len(snapshots) > 0   

        # 5. Check vibe summary (computed view)
        vibe_res = await client.get(f"/api/businesses/vibe/{business_id}")
        assert vibe_res.status_code == 200

        data = vibe_res.json()

        assert data["business_id"] == business_id
        assert data["review_count"] == 3
        assert "vibe_label" in data
        assert "avg_score" in data
        assert "summary_text" in data


         # 6. ABSA validation 
        aspect_res = await client.get(f"/api/reviews/{review_ids[0]}/aspects")

        assert aspect_res.status_code == 200
        rows = aspect_res.json()

        assert len(rows) > 0
        assert any(r["aspect"] for r in rows)
        assert any(r["sentiment_label"] in ["positive", "negative"] for r in rows)