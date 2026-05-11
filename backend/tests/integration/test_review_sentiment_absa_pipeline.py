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
