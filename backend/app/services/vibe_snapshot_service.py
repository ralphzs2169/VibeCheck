# This module manages Vibe Snapshots, which are periodic aggregated summaries of a business’s review sentiment.
# It handles retrieval, creation, and pipeline execution for generating vibe analytics over time.

import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from backend.app.core.ml_registry import MLRegistry
from backend.app.models.vibe_snapshot import VibeSnapshot
from backend.app.services.vibe_service import (
    compute_vibe_summary,
    convert_sentiment_to_vibe_score,
)


async def get_vibe_snapshot_or_404(db: AsyncSession, snapshot_id: int) -> VibeSnapshot:
    """
    Fetch a single vibe snapshot by ID or raise 404 if not found.
    """

    # query snapshot by primary key
    result = await db.execute(
        select(VibeSnapshot).where(VibeSnapshot.id == snapshot_id)
    )

    snapshot = result.scalars().first()

    # enforce existence check for API safety
    if not snapshot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vibe Snapshot not found",
        )

    return snapshot


async def get_vibe_snapshots_for_business(
    db: AsyncSession,
    business_id: int
) -> list[VibeSnapshot]:
    """
    Retrieve all snapshots for a business ordered by newest first.
    """

    # fetch all snapshots for business sorted by date descending
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
    """
    Generate and persist a single vibe snapshot from computed review analytics.
    """

    # compute aggregated sentiment + summary for business at given time
    data = await compute_vibe_summary(
        db,
        business_id,
        models,
        as_of_date=snapshot_date,
        allow_insufficient_data=True,
        use_ai_summary=use_ai_summary,
    )

    # skip snapshot creation if there is no usable data
    if data.get("status") == "insufficient_data":
        return None

    # build snapshot entity from computed analytics
    snapshot = VibeSnapshot(
        business_id=business_id,
        vibe_score=convert_sentiment_to_vibe_score(data["avg_score"]),
        vibe_label=data["vibe_label"],
        review_count=data["review_count"],
        positive_count=data["score_distribution"]["positive"],
        negative_count=data["score_distribution"]["negative"],
        summary_text=data["summary_text"],
        snapshot_date=snapshot_date,
    )

    # stage snapshot for DB insertion
    db.add(snapshot)

    # flush to generate ID without committing transaction
    await db.flush()

    return snapshot


async def get_latest_vibe_snapshot(db: AsyncSession, business_id: int):
    """
    Retrieve the most recent snapshot for a business.
    """

    # fetch latest snapshot by date
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
    """
    Executes full snapshot pipeline: compute + persist + commit.
    """

    # create snapshot from computed analytics
    snapshot = await create_vibe_snapshot(
        db,
        business_id,
        models,
        snapshot_date,
        use_ai_summary,
    )

    # commit only if snapshot was successfully created
    if snapshot:
        await db.commit()
        await db.refresh(snapshot)

    return snapshot