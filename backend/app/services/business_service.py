from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.core.ml_registry import MLRegistry
from backend.app.models.business import Business
from backend.app.models.review import Review
from backend.app.models.user import User
from backend.app.models.vibe_snapshot import VibeSnapshot
from backend.app.schemas.business import BusinessCreate, BusinessUpdate
from backend.app.services.vibe_snapshot_service import (
    create_vibe_snapshot,
    get_vibe_snapshots_for_business,
    get_latest_vibe_snapshot
)
from backend.app.services import business_service


async def create_business(
    db: AsyncSession,
    business: BusinessCreate,
    owner_id: int | None = None
) -> Business:
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
        owner_id=owner_id,
    )

    db.add(new_business)
    await db.commit()
    await db.refresh(new_business)
    return new_business


async def get_business_or_404(db: AsyncSession, business_id: int) -> Business:
    result = await db.execute(select(Business).where(Business.id == business_id))
    business = result.scalars().first()

    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Business not found"
        )

    return business


async def get_business_by_id(db: AsyncSession, business_id: int) -> Business | None:
    result = await db.execute(select(Business).where(Business.id == business_id))
    return result.scalars().first()


async def get_all_businesses(db: AsyncSession) -> list[Business]:
    result = await db.execute(select(Business))
    return result.scalars().all()


async def get_business_review_count(
        db: AsyncSession,
        business_id: int
    ) -> int:

        stmt = (
            select(func.count(Review.id))
            .where(Review.business_id == business_id)
        )

        result = await db.execute(stmt)
        count = result.scalar()

        return count or 0
    
async def get_business_homepage_feed(db: AsyncSession):

    latest_subquery = (
        select(
            VibeSnapshot.business_id,
            func.max(VibeSnapshot.snapshot_date).label("latest_date")
        )
        .group_by(VibeSnapshot.business_id)
        .subquery()
    )

    query = (
        select(Business, VibeSnapshot)
        .outerjoin(
            latest_subquery,
            Business.id == latest_subquery.c.business_id
        )
        .outerjoin(
            VibeSnapshot,
            (VibeSnapshot.business_id == latest_subquery.c.business_id) &
            (VibeSnapshot.snapshot_date == latest_subquery.c.latest_date)
        )
    )

    result = await db.execute(query)

    rows = result.all()

    response_data = []

    for business, vibe in rows:
        review_count = await business_service.get_business_review_count(db, business.id)
        response_data.append({
            "id": business.id,
            "name": business.name,
            "location": business.location,
            "short_description": business.short_description,
            "image_path": business.image_path,
            "created_at": business.created_at,
            "updated_at": business.updated_at,
            "review_count": review_count,
            "latest_vibe": (
                {
                    "vibe_score": vibe.vibe_score,
                    "vibe_label": vibe.vibe_label,
                    "review_count": vibe.review_count,
                    "summary_text": vibe.summary_text,
                    "positive_count": vibe.positive_count,
                    "mixed_count": vibe.mixed_count,
                    "negative_count": vibe.negative_count,
                }
                if vibe else None
            )
        })

    return response_data


async def verify_business_ownership(
    db: AsyncSession,
    business_id: int,
    user_id: int
) -> Business:

    business = await get_business_by_id(db, business_id)

    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business not found"
        )

    if business.owner_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized"
        )

    return business


def resolve_user_business_id(user: User, business_id: int | None) -> int:
        if business_id is not None:
            return business_id

        if not user.business:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No business found for user"
            )

        return user.business.id


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


# -------------------------
# BUSINESS REVIEW SERVICES
# -------------------------
async def get_business_profile(db: AsyncSession, business_id: int) -> dict:

    result = await db.execute(
        select(Business)
        .where(Business.id == business_id)
        .options(
            selectinload(Business.reviews).selectinload(Review.user),
            selectinload(Business.reviews).selectinload(Review.aspect_sentiments),
        )
    )

    business = result.scalars().first()

    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business not found"
        )

    latest_vibe = await get_latest_vibe_snapshot(db, business_id)

    return {
        "id": business.id,
        "name": business.name,
        "location": business.location,
        "short_description": business.short_description,
        "image_path": business.image_path,
        "created_at": business.created_at,
        "updated_at": business.updated_at,

        "latest_vibe": latest_vibe,

        "reviews": business.reviews,
    }


# -------------------------
# BUSINESS VIBE SERVICES
# -------------------------


async def get_business_vibe_snapshots(db: AsyncSession, business_id: int):
    # ensure business exists
    await get_business_or_404(db, business_id)

    # delegate to snapshot service
    return await get_vibe_snapshots_for_business(db, business_id)


# async def get_business_latest_vibe(
#     db: AsyncSession, business_id: int, models: MLRegistry
# ) -> dict:

#     await get_business_or_404(db, business_id)

#     # Compute vibe summary on-the-fly from current reviews
#     # This ensures real-time vibe data with all fields (avg_score, score_distribution, etc.)
#     vibe_data = await compute_vibe_summary(
#         db,
#         business_id,
#         models,
#         as_of_date=None,  # None = use all reviews up to now
#         allow_insufficient_data=False,  # Return insufficient_data status if < minimum reviews
#     )

#     return vibe_data


async def run_vibe_snapshot_pipeline(
    db: AsyncSession,
    business_id: int,
    models: MLRegistry,
    snapshot_date: datetime.datetime,
    use_ai_summary: bool = False,
) -> VibeSnapshot | None:
    snapshot = await create_vibe_snapshot(
        db, business_id, models, snapshot_date, use_ai_summary
    )
    if snapshot:
        await db.commit()
        await db.refresh(snapshot)
    return snapshot


# -------------------------
# BUSINESS ABSA SERVICES
# -------------------------
