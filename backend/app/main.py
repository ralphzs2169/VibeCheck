from fastapi import FastAPI
from contextlib import asynccontextmanager

from backend.app.routers import users, businesses
from backend.app.core.database import engine, Base

# Handle startup and shutdown events
@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown
    await engine.dispose()


app = FastAPI(lifespan=lifespan)

app.include_router(users.router, prefix="/api/users", tags=["users"])
# app.include_router(reviews.router, prefix="/api/reviews", tags=["reviews"])
app.include_router(businesses.router, prefix="/api/businesses", tags=["businesses"])

@app.get("/")
async def root():
    return {"message": "Welcome to the Blog API!"}
