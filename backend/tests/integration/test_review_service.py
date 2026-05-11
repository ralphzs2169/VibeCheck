from datetime import UTC, datetime, timedelta

import pytest
import pytest_asyncio
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from backend.app.core.database import Base
from backend.app.models.business import Business
from backend.app.models.review import Review
from backend.app.models.user import User
from backend.app.schemas.review import ReviewCreate, ReviewUpdate
from backend.app.services.review_service import (
	create_review,
	delete_review,
	get_all_reviews,
	get_latest_reviews_for_business,
	get_review_or_404,
	update_review,
)


class DummyModels:
	def __init__(self):
		self.sentiment = object()


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
async def db_session(test_engine):
	session_factory = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
	async with session_factory() as session:
		yield session
		await session.rollback()


@pytest_asyncio.fixture(autouse=True)
async def clear_tables(test_engine):
	async with test_engine.begin() as conn:
		await conn.execute(Review.__table__.delete())
		await conn.execute(Business.__table__.delete())
		await conn.execute(User.__table__.delete())


async def seed_user_and_business(db: AsyncSession, suffix: str = "") -> tuple[User, User, Business]:
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
		name=f"Business {suffix}",
		location="Cebu",
		short_description="Integration test business",
		image_path=None,
		owner_id=owner.id,
	)
	db.add(business)
	await db.flush()
	await db.commit()

	return owner, reviewer, business


@pytest.mark.asyncio
async def test_create_review_persists_sentiment_and_relations(db_session, monkeypatch):
	monkeypatch.setattr(
		"backend.app.services.review_service.analyze_sentiment",
		lambda content, model: (0.73, "positive", 0.98),
	)

	async def fake_run_absa_for_review(db, review, models):
		return None

	monkeypatch.setattr(
		"backend.app.services.review_service.run_absa_for_review",
		fake_run_absa_for_review,
	)

	_, reviewer, business = await seed_user_and_business(db_session, "create")

	payload = ReviewCreate(content="Great resort experience", business_id=business.id)
	review = await create_review(db_session, payload, reviewer.id, DummyModels())

	assert review.id is not None
	assert review.content == "Great resort experience"
	assert review.sentiment_score == pytest.approx(0.73)
	assert review.sentiment_label == "positive"
	assert review.user_id == reviewer.id
	assert review.business_id == business.id
	assert review.user is not None


@pytest.mark.asyncio
async def test_get_review_or_404_raises_for_missing_review(db_session):
	with pytest.raises(HTTPException) as exc:
		await get_review_or_404(db_session, 999999)

	assert exc.value.status_code == 404
	assert exc.value.detail == "Review not found"


@pytest.mark.asyncio
async def test_update_and_delete_review(db_session, monkeypatch):
	monkeypatch.setattr(
		"backend.app.services.review_service.analyze_sentiment",
		lambda content, model: (0.25, "positive", 0.9),
	)

	async def fake_run_absa_for_review(db, review, models):
		return None

	monkeypatch.setattr(
		"backend.app.services.review_service.run_absa_for_review",
		fake_run_absa_for_review,
	)

	_, reviewer, business = await seed_user_and_business(db_session, "update_delete")

	created = await create_review(
		db_session,
		ReviewCreate(content="Initial text", business_id=business.id),
		reviewer.id,
		DummyModels(),
	)

	updated = await update_review(
		db_session,
		created.id,
		ReviewUpdate(content="Updated review content"),
	)
	assert updated.content == "Updated review content"

	await delete_review(db_session, created.id)
	with pytest.raises(HTTPException):
		await get_review_or_404(db_session, created.id)


@pytest.mark.asyncio
async def test_get_latest_reviews_for_business_returns_desc_and_limited(db_session):
	_, reviewer, business = await seed_user_and_business(db_session, "latest")

	base_time = datetime.now(UTC)
	for i in range(4):
		db_session.add(
			Review(
				content=f"review {i}",
				sentiment_score=0.1 * i,
				sentiment_label="positive",
				business_id=business.id,
				user_id=reviewer.id,
				created_at=base_time + timedelta(minutes=i),
			)
		)
	await db_session.commit()

	latest = await get_latest_reviews_for_business(db_session, business.id, limit=3)

	assert len(latest) == 3
	assert latest[0].content == "review 3"
	assert latest[1].content == "review 2"
	assert latest[2].content == "review 1"
	assert all(r.user is not None for r in latest)


@pytest.mark.asyncio
async def test_get_all_reviews_returns_created_rows(db_session, monkeypatch):
	monkeypatch.setattr(
		"backend.app.services.review_service.analyze_sentiment",
		lambda content, model: (0.1, "positive", 0.9),
	)

	async def fake_run_absa_for_review(db, review, models):
		return None

	monkeypatch.setattr(
		"backend.app.services.review_service.run_absa_for_review",
		fake_run_absa_for_review,
	)

	_, reviewer, business = await seed_user_and_business(db_session, "all")

	await create_review(
		db_session,
		ReviewCreate(content="First", business_id=business.id),
		reviewer.id,
		DummyModels(),
	)
	await create_review(
		db_session,
		ReviewCreate(content="Second", business_id=business.id),
		reviewer.id,
		DummyModels(),
	)

	all_reviews = await get_all_reviews(db_session)
	assert len(all_reviews) == 2
