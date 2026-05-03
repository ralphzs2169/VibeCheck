from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI

from backend.app.core.constants import HOURS_BETWEEN_SNAPSHOTS
from backend.app.core.database import Base, engine
from backend.app.core.scheduler import run_vibe_snapshot_job, scheduler
from backend.app.routers import analytics, businesses, reviews, users

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

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

app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(reviews.router, prefix="/api/reviews", tags=["reviews"])
app.include_router(businesses.router, prefix="/api/businesses", tags=["businesses"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])



@app.get("/")
async def root():
    return {"message": "Welcome to Mobile Legends!"}



