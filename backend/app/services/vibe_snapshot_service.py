import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.ml_registry import MLRegistry
from backend.app.models.vibe_snapshot import VibeSnapshot
from backend.app.services.vibe_service import compute_vibe_summary
from backend.app.services.vibe_service import convert_sentiment_to_vibe_score
from fastapi import HTTPException, status


async def get_vibe_snapshot_or_404(db: AsyncSession, snapshot_id: int) -> VibeSnapshot:
    result = await db.execute(select(VibeSnapshot).where(VibeSnapshot.id == snapshot_id))
    snapshot = result.scalars().first()

    if not snapshot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vibe Snapshot not found")

    return snapshot


async def get_vibe_snapshots_for_business(
    db: AsyncSession,
    business_id: int
) -> list[VibeSnapshot]:

    result = await db.execute(
        select(VibeSnapshot)
        .where(VibeSnapshot.business_id == business_id)
        .order_by(VibeSnapshot.snapshot_date.desc())
    )

    return result.scalars().all()


async def create_vibe_snapshot(
    db: AsyncSession,
    business_id: int,
    models: MLRegistry,
    snapshot_date: datetime.datetime,
    use_ai_summary: bool = False
) -> VibeSnapshot | None:

    data = await compute_vibe_summary(
        db,
        business_id,
        models,
        as_of_date=snapshot_date,
        allow_insufficient_data=True,  # Always create snapshots for analytics, even with few reviews
        use_ai_summary=use_ai_summary
    )

    if data.get("status") == "insufficient_data":
        return None

    snapshot = VibeSnapshot(
        business_id=business_id,
        vibe_score=convert_sentiment_to_vibe_score(data["avg_score"]),
        vibe_label=data["vibe_label"],
        review_count=data["review_count"],
        positive_count=data["score_distribution"]["positive"],
        mixed_count=data["score_distribution"]["mixed"],
        negative_count=data["score_distribution"]["negative"],
        summary_text=data["summary_text"],
        snapshot_date=snapshot_date
    )
    

    db.add(snapshot)
    await db.flush()

    return snapshot


async def get_latest_vibe_snapshot(db: AsyncSession, business_id: int):
    result = await db.execute(
        select(VibeSnapshot)
        .where(VibeSnapshot.business_id == business_id)
        .order_by(VibeSnapshot.snapshot_date.desc())
        .limit(1)
    )

    return result.scalars().first()

async def run_vibe_snapshot_pipeline(
    db: AsyncSession,
    business_id: int,
    models: MLRegistry,
    snapshot_date: datetime.datetime,
    use_ai_summary: bool = False
) -> VibeSnapshot | None:
    snapshot = await create_vibe_snapshot(db, business_id, models, snapshot_date, use_ai_summary)
    if snapshot:
        await db.commit()
        await db.refresh(snapshot)
    return snapshot



