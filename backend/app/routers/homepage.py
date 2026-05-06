from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.database import get_db
from backend.app.services.business_service import get_business_homepage_feed

router = APIRouter()

@router.get("")
async def get_homepage(db: AsyncSession = Depends(get_db)):
    data = await get_business_homepage_feed(db)
    return {"businesses": data}