from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.models.vibe_snapshot import VibeSnapshot
from backend.app.services.vibe_service import compute_vibe_summary


async def create_vibe_snapshot(db: AsyncSession, business_id: int):
    data = await compute_vibe_summary(db, business_id)

    if data.get("status") == "insufficient_data":
        return None

    snapshot = VibeSnapshot(
        business_id=business_id,
        avg_score=data["avg_score"],
        vibe_label=data["vibe_label"],
        review_count=data["review_count"],
        positive_count=data["score_distribution"]["positive"],
        mixed_count=data["score_distribution"]["mixed"],
        negative_count=data["score_distribution"]["negative"],
    )

    db.add(snapshot)
    await db.commit()
    await db.refresh(snapshot)

    return snapshot
