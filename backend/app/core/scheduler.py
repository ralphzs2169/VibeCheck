import datetime
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select
from transformers import pipeline
from sentence_transformers import SentenceTransformer

from backend.app.core.database import AsyncSessionLocal
from backend.app.core.ml_registry import MLRegistry
from backend.app.core.aspects import ASPECTS
from backend.app.models.business import Business
from backend.app.services.vibe_snapshot_service import create_vibe_snapshot

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def run_vibe_snapshot_job():
    logger.info("VibeSnapshot Job START")

    try:
        # Load ML models for the job
        sentiment_model = pipeline(
            "sentiment-analysis",
            model="distilbert-base-uncased-finetuned-sst-2-english"
        )
        embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
        aspect_texts = list(ASPECTS.values())
        aspect_embeddings = embedding_model.encode(aspect_texts, convert_to_tensor=True)
        models = MLRegistry(
            sentiment=sentiment_model,
            embedding=embedding_model,
            aspect_embeddings=aspect_embeddings
        )

        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Business))

            businesses = result.scalars().all()
            
            now = datetime.datetime.now(datetime.timezone.utc)
            for business in businesses:
                await create_vibe_snapshot(db, business.id, models, now)

            await db.commit()

        logger.info("VibeSnapshot Job FINISHED")

    except Exception as e:
        logger.exception(f"VibeSnapshot Job FAILED: {e}")