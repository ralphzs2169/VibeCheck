from contextlib import asynccontextmanager
import logging
import os

from dotenv import load_dotenv
from fastapi import FastAPI
from keybert import KeyBERT

from backend.app.core.aspects import ASPECTS
from backend.app.core.constants import HOURS_BETWEEN_SNAPSHOTS
from backend.app.core.database import Base, engine
from backend.app.core.scheduler import run_vibe_snapshot_job, scheduler
from backend.app.routers import analytics, businesses, reviews, users

from transformers import pipeline
from sentence_transformers import SentenceTransformer

from backend.app.core.ml_registry import MLRegistry


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)

# Suppress verbose logging from dependencies
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("sentence_transformers").setLevel(logging.WARNING)
logging.getLogger("transformers").setLevel(logging.WARNING)



# lifespan function to handle startup and shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):

    load_dotenv()
    hf_token = os.getenv("HF_TOKEN")

    # Database Initialization
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # ML model loading
    sentiment_model = pipeline(
        "sentiment-analysis",
        model="distilbert-base-uncased-finetuned-sst-2-english",
        use_auth_token=hf_token
    )

    embedding_model = SentenceTransformer(
        "all-MiniLM-L6-v2"
    )

    # pre-compute aspect embeddings for efficient similarity calculations during ABSA
    aspect_texts = list(ASPECTS.values())
    aspect_embeddings = embedding_model.encode(
        aspect_texts,
        convert_to_tensor=True
    )

    app.state.models = MLRegistry(
        sentiment=sentiment_model,
        embedding=embedding_model,
        aspect_embeddings=aspect_embeddings,
        keyword_extractor=KeyBERT()
    )

    logging.info("ML models loaded successfully")

    # VibeSnapshot Scheduler setup
    scheduler.add_job(
        run_vibe_snapshot_job,
        trigger="interval",
        hours=HOURS_BETWEEN_SNAPSHOTS,
    )

    scheduler.start()

    logging.info("Scheduler started")
    logging.info(f"Jobs: {scheduler.get_jobs()}")

    yield

    # Shutdown 
    scheduler.shutdown()
    await engine.dispose()


app = FastAPI(lifespan=lifespan)


# Routes
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(reviews.router, prefix="/api/reviews", tags=["reviews"])
app.include_router(businesses.router, prefix="/api/businesses", tags=["businesses"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])

@app.get("/")
async def root():
    return {"message": "Welcome to Mobile Legends!"}