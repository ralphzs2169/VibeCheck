from contextlib import asynccontextmanager
import logging
import os

from dotenv import load_dotenv
from fastapi import FastAPI
from keybert import KeyBERT
from openai import OpenAI

from backend.app.core.aspects import ASPECTS
from backend.app.core.constants import HOURS_BETWEEN_SNAPSHOTS
from backend.app.core.database import Base, engine
from backend.app.core.scheduler import run_vibe_snapshot_job, scheduler
from backend.app.routers import analytics, businesses, reviews, users, vibe_snapshots

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

    # Initialize KeyBERT with the same embedding model for consistent vector representations
    keyword_extractor_model = KeyBERT(model=embedding_model)

    # Initialize Gemini model
    llm_api_key = os.getenv("LLM_API_KEY")

    if not llm_api_key:
        raise ValueError("LLM_API_KEY is missing")

    llm_client = OpenAI(
        api_key=llm_api_key,
        base_url="https://api.groq.com/openai/v1"
    )

    app.state.models = MLRegistry(
        sentiment=sentiment_model,
        embedding=embedding_model,
        aspect_embeddings=aspect_embeddings,
        keyword_extractor=keyword_extractor_model,
        large_language_model=llm_client
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
app.include_router(vibe_snapshots.router, prefix="/api/vibe-snapshots", tags=["vibe_snapshots"])

@app.get("/")
async def root():
    return {"message": "Welcome to Mobile Legends!"}