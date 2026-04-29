from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from backend.app.models.business import Business

async def get_business_or_404(db: AsyncSession, business_id: int):
    result = await db.execute(
        select(Business).where(Business.id == business_id)
    )
    business = result.scalars().first()

    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business not found",
        )

    return business