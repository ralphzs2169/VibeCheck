import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app
from transformers import pipeline
from sentence_transformers import SentenceTransformer
from backend.app.core.ml_registry import MLRegistry
from backend.app.core.aspects import ASPECTS


@pytest.mark.asyncio
async def test_review_triggers_absa_pipeline():
    # Initialize ML models if not already done
    if not hasattr(app.state, "models"):
        sentiment_model = pipeline(
            "sentiment-analysis",
            model="distilbert-base-uncased-finetuned-sst-2-english"
        )
        embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
        aspect_texts = list(ASPECTS.values())
        aspect_embeddings = embedding_model.encode(aspect_texts, convert_to_tensor=True)
        app.state.models = MLRegistry(
            sentiment=sentiment_model,
            embedding=embedding_model,
            aspect_embeddings=aspect_embeddings
        )

    transport = ASGITransport(app=app)
    
    async with AsyncClient(transport=transport, base_url="http://test") as client:

        # 1. Create user
        user_res = await client.post("/api/users", json={
            "username": "absa_user",
            "firstname": "ABSA",
            "lastname": "Tester"
        })
        assert user_res.status_code == 201
        user_id = user_res.json()["id"]

        # 2. Create business
        biz_res = await client.post("/api/businesses", json={
            "name": "ABSA Cafe",
            "location": "Cebu",
            "short_description": "Testing ABSA",
            "image_path": None
        })
        assert biz_res.status_code == 201
        business_id = biz_res.json()["id"]

        # 3. Create review (THIS triggers ABSA internally)
        review_res = await client.post("/api/reviews", json={
            "content": "Food is bad, service is slow, parking is terrible",
            "user_id": user_id,
            "business_id": business_id
        })

        assert review_res.status_code == 201
        review_id = review_res.json()["id"]

        # 4. Fetch ABSA results from API (you need this endpoint OR DB-backed endpoint)
        absa_res = await client.get(f"/api/reviews/{review_id}/aspects")

        assert absa_res.status_code == 200

        data = absa_res.json()

        # Should detect multiple aspects
        aspects = [item["aspect"] for item in data]

        assert "service" in aspects or "food" in aspects
        assert len(data) >= 2  # multiple aspects expected