import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select

from backend.app.core.database import AsyncSessionLocal
from backend.app.models.business import Business
from backend.app.services.vibe_snapshot_service import create_vibe_snapshot

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def run_vibe_snapshot_job():
    logger.info("VibeSnapshot Job START")

    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Business))
            businesses = result.scalars().all()

            for business in businesses:
                await create_vibe_snapshot(db, business.id)

            await db.commit()

        logger.info("VibeSnapshot Job FINISHED")

    except Exception as e:
        logger.exception(f"VibeSnapshot Job FAILED: {e}")