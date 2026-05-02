import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.models.vibe_snapshot import VibeSnapshot
from backend.app.services.vibe_service import compute_vibe_summary
from backend.app.services.vibe_service import convert_sentiment_to_vibe_score


async def create_vibe_snapshot(
    db: AsyncSession,
    business_id: int,
    snapshot_date: datetime.datetime,
) -> VibeSnapshot | None:

    data = await compute_vibe_summary(
        db,
        business_id,
        as_of_date=snapshot_date,
        allow_insufficient_data=True  # Always create snapshots for analytics, even with few reviews
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
        snapshot_date=snapshot_date
    )

    db.add(snapshot)
    await db.flush()

    return snapshot

