from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from sqlalchemy.orm import selectinload
from collections.abc import Sequence

from backend.app.models.business import Business
from backend.app.models.review import Review
from backend.app.models.vibe_snapshot import VibeSnapshot
from backend.app.services.vibe_service import compute_vibe_summary
from backend.app.schemas.business import BusinessCreate, BusinessUpdate


async def create_business(db: AsyncSession, business: BusinessCreate) -> Business:
    result = await db.execute(select(Business).where(Business.name == business.name))
    existing = result.scalars().first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Business Name already exists",
        )

    new_business = Business(
        name=business.name,
        location=business.location,
        short_description=business.short_description,
        image_path=business.image_path,
    )

    db.add(new_business)
    await db.commit()
    await db.refresh(new_business)
    return new_business


async def get_business_or_404(db: AsyncSession, business_id: int) -> Business:
    result = await db.execute(
        select(Business).where(Business.id == business_id)
    )
    business = result.scalars().first()

    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business not found"
        )

    return business


async def get_all_businesses(db: AsyncSession) -> Sequence[Business]:
    result = await db.execute(select(Business))
    return result.scalars().all()


async def get_businesses_by_owner(
    db: AsyncSession, owner_id: int
) -> Sequence[Business]:
    result = await db.execute(
        select(Business).where(Business.owner_id == owner_id)
    )
    return result.scalars().all()


async def update_business(
    db: AsyncSession, business_id: int, data: BusinessUpdate
) -> Business:
    business = await get_business_or_404(db, business_id)

    update_data = data.model_dump(exclude_unset=True)

    if "name" in update_data and update_data["name"] != business.name:
        result = await db.execute(
            select(Business).where(Business.name == update_data["name"])
        )
        existing = result.scalars().first()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Business name already exists",
            )

    for k, v in update_data.items():
        setattr(business, k, v)

    await db.commit()
    await db.refresh(business)
    return business


async def delete_business(db: AsyncSession, business_id: int) -> None:
    business = await get_business_or_404(db, business_id)
    await db.delete(business)
    await db.commit()


# ── Business Reviews ──────────────────────────────────────────────────────────
async def get_business_with_reviews(
    db: AsyncSession, business_id: int
) -> Business:
    result = await db.execute(
        select(Business)
        .where(Business.id == business_id)
        .options(selectinload(Business.reviews))
    )
    business = result.scalars().first()

    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business not found"
        )

    return business


# ── Business Vibe ─────────────────────────────────────────────────────────────
async def get_business_vibe(db: AsyncSession, business_id: int) -> dict:
    await get_business_or_404(db, business_id)

    result = await db.execute(
        select(Review.content).where(Review.business_id == business_id)
    )
    reviews = [r[0] for r in result.all()]

    if not reviews:
        return {
            "status": "no_reviews",
            "message": "No reviews yet. Be the first to share your experience!",
        }

    return await compute_vibe_summary(db, business_id)


async def get_vibe_snapshots(
    db: AsyncSession, business_id: int
) -> Sequence[VibeSnapshot]:
    await get_business_or_404(db, business_id)

    result = await db.execute(
        select(VibeSnapshot).where(VibeSnapshot.business_id == business_id)
    )
    return result.scalars().all()