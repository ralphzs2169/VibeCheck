import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

import backend.app.models  # noqa: F401
import backend.app.services.auth_service as auth_service
from backend.app.core.database import Base, get_db
from backend.app.main import app
from backend.app.models.aspect_sentiment import AspectSentiment
from backend.app.models.business import Business
from backend.app.models.review import Review
from backend.app.models.user import User


class DummyModels:
    def __init__(self):
        self.sentiment = object()
        self.embedding = object()
        self.aspect_embeddings = object()


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def session_factory(test_engine):
    return async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture(autouse=True)
async def clear_tables(test_engine):
    async with test_engine.begin() as conn:
        await conn.execute(AspectSentiment.__table__.delete())
        await conn.execute(Review.__table__.delete())
        await conn.execute(Business.__table__.delete())
        await conn.execute(User.__table__.delete())


async def seed_user_and_business(db: AsyncSession, suffix: str = "pipeline") -> tuple[User, Business]:
    owner = User(
        username=f"owner_{suffix}",
        firstname="Owner",
        lastname="Test",
        role="owner",
        hashed_password="hashed",
    )
    reviewer = User(
        username=f"reviewer_{suffix}",
        firstname="Reviewer",
        lastname="Test",
        role="reviewer",
        hashed_password="hashed",
    )
    db.add(owner)
    db.add(reviewer)
    await db.flush()

    business = Business(
        name=f"Pipeline Business {suffix}",
        location="Cebu",
        short_description="Pipeline integration",
        image_path=None,
        owner_id=owner.id,
    )
    db.add(business)
    await db.commit()
    await db.refresh(reviewer)
    await db.refresh(business)
    return reviewer, business


@pytest.mark.asyncio
async def test_review_sentiment_absa_db_api_pipeline(session_factory, monkeypatch):
    async with session_factory() as db:
        reviewer, business = await seed_user_and_business(db)

    # Deterministic sentiment for Review -> Sentiment stage
    monkeypatch.setattr(
        "backend.app.services.review_service.analyze_sentiment",
        lambda content, model: (0.84, "positive", 0.97),
    )

    # Deterministic aspect detection for ABSA stage
    def fake_detect_aspects(sentence, models):
        text = sentence.lower()
        if "service" in text:
            return [("service", 0.91)]
        if "food" in text:
            return [("food", 0.87)]
        return [("general", 0.5)]

    monkeypatch.setattr("backend.app.services.absa_service.detect_aspects", fake_detect_aspects)
    monkeypatch.setattr(
        "backend.app.services.absa_service.analyze_sentiment",
        lambda text, model: (0.78, "positive", 0.96),
    )

    app.state.models = DummyModels()

    async def override_get_db():
        async with session_factory() as session:
            yield session

    async def override_user():
        return reviewer

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[auth_service.get_authenticated_user] = override_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        create_res = await client.post(
            "/api/reviews",
            json={
                "content": "Service was excellent. Food quality was great.",
                "business_id": business.id,
            },
        )

        assert create_res.status_code == 201
        created = create_res.json()

        # API response from create_review should include sentiment + aspects
        assert created["sentiment_label"] == "positive"
        assert created["sentiment_score"] == pytest.approx(0.84)
        assert created["user_id"] == reviewer.id
        assert created["business_id"] == business.id
        assert len(created["aspect_sentiments"]) == 2
        assert {a["aspect"] for a in created["aspect_sentiments"]} == {"service", "food"}

        review_id = created["id"]

        # ABSA route should return persisted aspect rows
        aspects_res = await client.get(f"/api/reviews/{review_id}/aspects")
        assert aspects_res.status_code == 200
        aspects = aspects_res.json()
        assert len(aspects) == 2
        assert {a["aspect"] for a in aspects} == {"service", "food"}

        # Generic review fetch should include nested aspect sentiments
        get_res = await client.get(f"/api/reviews/{review_id}")
        assert get_res.status_code == 200
        fetched = get_res.json()
        assert fetched["id"] == review_id
        assert fetched["sentiment_label"] == "positive"
        assert len(fetched["aspect_sentiments"]) == 2

    # DB-level verification of persisted rows
    async with session_factory() as db:
        saved_review = (await db.execute(select(Review).where(Review.id == review_id))).scalars().first()
        saved_aspects = (await db.execute(select(AspectSentiment).where(AspectSentiment.review_id == review_id))).scalars().all()

        assert saved_review is not None
        assert saved_review.sentiment_label == "positive"
        assert saved_review.sentiment_score == pytest.approx(0.84)
        assert len(saved_aspects) == 2

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_review_update_with_sentiment_absa_reanalysis(session_factory, monkeypatch):
    """
    Integration test for review update flow:
    1. Create review with initial content and sentiment + ABSA analysis
    2. Update review content
    3. Verify sentiment is re-analyzed
    4. Verify old aspect sentiments are deleted
    5. Verify new aspect sentiments are created
    """
    async with session_factory() as db:
        reviewer, business = await seed_user_and_business(db, suffix="update_pipeline")

    # Initial sentiment for "Service was great"
    def fake_analyze_sentiment(content, model):
        if "terrible" in content.lower() or "bad" in content.lower():
            return (-0.82, "negative", 0.95)
        return (0.85, "positive", 0.97)

    # Aspect detection based on content
    def fake_detect_aspects(sentence, models):
        text = sentence.lower()
        aspects = []
        if "service" in text:
            aspects.append(("service", 0.91))
        if "food" in text:
            aspects.append(("food", 0.88))
        return aspects

    monkeypatch.setattr(
        "backend.app.services.review_service.analyze_sentiment",
        fake_analyze_sentiment,
    )
    monkeypatch.setattr(
        "backend.app.services.absa_service.detect_aspects",
        fake_detect_aspects,
    )
    monkeypatch.setattr(
        "backend.app.services.absa_service.analyze_sentiment",
        lambda text, model: (-0.82, "negative", 0.96) if "terrible" in text.lower() else (0.80, "positive", 0.96),
    )

    app.state.models = DummyModels()

    async def override_get_db():
        async with session_factory() as session:
            yield session

    async def override_user():
        return reviewer

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[auth_service.get_authenticated_user] = override_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. CREATE REVIEW with initial content
        create_res = await client.post(
            "/api/reviews",
            json={
                "content": "Service was great. Staff was helpful.",
                "business_id": business.id,
            },
        )
        assert create_res.status_code == 201
        created = create_res.json()
        review_id = created["id"]

        # Verify initial state: positive sentiment, service aspect detected
        assert created["sentiment_label"] == "positive"
        assert created["sentiment_score"] == pytest.approx(0.85)
        assert len(created["aspect_sentiments"]) == 1
        assert created["aspect_sentiments"][0]["aspect"] == "service"

        # DB verification before update
        async with session_factory() as db:
            aspects_before = (
                await db.execute(
                    select(AspectSentiment).where(AspectSentiment.review_id == review_id)
                )
            ).scalars().all()
            assert len(aspects_before) == 1, f"Expected 1 aspect before update, got {len(aspects_before)}"
            assert aspects_before[0].aspect == "service"
            old_aspect_count = len(aspects_before)

        # 2. UPDATE REVIEW with new content
        update_res = await client.patch(
            f"/api/reviews/{review_id}",
            json={
                "content": "Food quality was terrible. Service was okay.",
            },
        )
        assert update_res.status_code == 200
        updated = update_res.json()

        # Verify sentiment changed to negative
        assert updated["sentiment_label"] == "negative"
        assert updated["sentiment_score"] == pytest.approx(-0.82)

        # Verify aspects were re-analyzed: should now include both food and service
        assert len(updated["aspect_sentiments"]) == 2, f"Expected 2 aspects after update, got {len(updated['aspect_sentiments'])}"
        aspect_names = {a["aspect"] for a in updated["aspect_sentiments"]}
        assert aspect_names == {"food", "service"}

        # 3. DB-LEVEL VERIFICATION: old aspects were deleted, new ones created
        async with session_factory() as db:
            saved_review = (
                await db.execute(select(Review).where(Review.id == review_id))
            ).scalars().first()
            saved_aspects = (
                await db.execute(
                    select(AspectSentiment).where(AspectSentiment.review_id == review_id)
                )
            ).scalars().all()

            # Verify review sentiment updated
            assert saved_review.sentiment_label == "negative"
            assert saved_review.sentiment_score == pytest.approx(-0.82)

            # Verify old aspects were deleted (should only have new ones now)
            saved_aspect_names = {a.aspect for a in saved_aspects}
            assert saved_aspect_names == {"food", "service"}, f"Expected only {{food, service}}, got {saved_aspect_names}"

            # Verify we have exactly 2 aspects (not 1 old + 2 new = 3)
            assert len(saved_aspects) == 2, f"Expected 2 aspects after update (old deleted + 2 new), got {len(saved_aspects)}"

        # 4. API-LEVEL VERIFICATION: fetch review should return new aspects
        get_res = await client.get(f"/api/reviews/{review_id}")
        assert get_res.status_code == 200
        fetched = get_res.json()
        assert fetched["sentiment_label"] == "negative"
        assert len(fetched["aspect_sentiments"]) == 2
        assert {a["aspect"] for a in fetched["aspect_sentiments"]} == {"food", "service"}

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_review_update_without_content_change_skips_reanalysis(session_factory, monkeypatch):
    """
    Integration test: updating a review without changing content should NOT re-run NLP.
    Only update fields like rating should not trigger sentiment/ABSA re-analysis.
    """
    async with session_factory() as db:
        reviewer, business = await seed_user_and_business(db, suffix="no_reanalysis")

    call_count = {"sentiment": 0, "absa": 0}

    def fake_analyze_sentiment(content, model):
        call_count["sentiment"] += 1
        return (0.80, "positive", 0.95)

    def fake_detect_aspects(sentence, models):
        call_count["absa"] += 1
        if "service" in sentence.lower():
            return [("service", 0.90)]
        return []

    monkeypatch.setattr(
        "backend.app.services.review_service.analyze_sentiment",
        fake_analyze_sentiment,
    )
    monkeypatch.setattr(
        "backend.app.services.absa_service.detect_aspects",
        fake_detect_aspects,
    )
    monkeypatch.setattr(
        "backend.app.services.absa_service.analyze_sentiment",
        lambda text, model: (0.80, "positive", 0.95),
    )

    app.state.models = DummyModels()

    async def override_get_db():
        async with session_factory() as session:
            yield session

    async def override_user():
        return reviewer

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[auth_service.get_authenticated_user] = override_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Create review
        create_res = await client.post(
            "/api/reviews",
            json={
                "content": "Service was excellent.",
                "business_id": business.id,
            },
        )
        assert create_res.status_code == 201
        created = create_res.json()
        review_id = created["id"]

        # Reset counters after creation
        call_count["sentiment"] = 0
        call_count["absa"] = 0

        # Update review without changing content (content field not included)
        update_res = await client.patch(
            f"/api/reviews/{review_id}",
            json={},  # Empty update payload
        )
        assert update_res.status_code == 200

        # Verify sentiment and ABSA were NOT re-run
        assert call_count["sentiment"] == 0, "Sentiment should not be re-analyzed without content change"
        assert call_count["absa"] == 0, "ABSA should not be re-run without content change"

    app.dependency_overrides.clear()
