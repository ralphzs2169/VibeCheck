from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.core.database import get_db
from backend.app.models.business import Business
from backend.app.schemas.business import (
    BusinessCreate,
    BusinessResponse,
    BusinessUpdate,
    BusinessWithReviewsResponse
)
from backend.app.services.business_service import get_business_or_404

router = APIRouter()

# Create Business
@router.post(
    "", 
    response_model=BusinessResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_business(business: BusinessCreate, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
        select(Business).where(Business.name == business.name),
    )
    existing_business = result.scalars().first()
    if existing_business:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Business Name already exists",
        )

    new_business = Business(
        name=business.name,
        location=business.location,
        short_description=business.short_description,
        image_path=business.image_path
    )
    db.add(new_business)
    await db.commit()
    await db.refresh(new_business)
    return new_business


# Get Business by ID
@router.get("/{business_id}", response_model=BusinessResponse)
async def get_business(
    business_id: int,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    business = await get_business_or_404(db, business_id)
    return business


# Get all Businesses
@router.get("", response_model=list[BusinessResponse])
async def get_businesses(db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
        select(Business).options(selectinload(Business.reviews))
    )
    businesses = result.scalars().all()
    return businesses


# Update Business
@router.patch("/{business_id}", response_model=BusinessResponse)
async def update_business(
    business_id: int,
    updated_business: BusinessUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    business = await get_business_or_404(db, business_id)

    update_data = updated_business.model_dump(exclude_unset=True)

    # Check business name conflict ONLY if name is being updated
    if "name" in update_data and update_data["name"] != business.name:
        result = await db.execute(
            select(Business).where(Business.name == update_data["name"]),
        )
        existing_business = result.scalars().first()

        if existing_business:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Business name already exists",
            )

    # Apply updates safely
    for field, value in update_data.items():
        setattr(business, field, value)

    await db.commit()
    await db.refresh(business)

    return business


# Delete Business
@router.delete("/{business_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_business(business_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    business = await get_business_or_404(db, business_id)

    await db.delete(business)
    await db.commit()


# Get Specific Business with Reviews
@router.get("/{business_id}/reviews", response_model=BusinessWithReviewsResponse)
async def get_business_with_reviews(
    business_id: int,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    result = await db.execute(
        select(Business).where(Business.id == business_id).options(selectinload(Business.reviews))
    )
    business = result.scalars().first()

    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business not found",
        )
    return business