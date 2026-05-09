import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

import backend.app.services.business_service as business_service
from backend.app.core.database import get_db
from backend.app.core.dependencies import get_models
from backend.app.core.ml_registry import MLRegistry
from backend.app.models.business import Business
from backend.app.schemas.business import (
    BusinessCreate,
    BusinessResponse,
    BusinessUpdate
)
from backend.app.schemas.vibe_snapshot import VibeSnapshotResponse

router = APIRouter()


# -------------------------
# CREATE BUSINESS
# -------------------------
@router.post(
    "",
    response_model=BusinessResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_business(
    business: BusinessCreate, db: Annotated[AsyncSession, Depends(get_db)]
) -> Business:
    return await business_service.create_business(db, business)


# -------------------------
# GET ALL BUSINESSES
# -------------------------
@router.get("")
async def get_businesses(
    db: Annotated[AsyncSession, Depends(get_db)],
    include_vibe: bool = True
):
    if include_vibe:
        return await business_service.get_all_businesses_with_latest_vibe(db)
    businesses = await business_service.get_all_businesses(db)
    return [BusinessResponse.model_validate(b) for b in businesses]



@router.get("/vibe_snapshots/{business_id}", response_model=list[VibeSnapshotResponse])
async def get_business_vibe_snapshots(
    business_id: int, db: Annotated[AsyncSession, Depends(get_db)]
) -> list[VibeSnapshotResponse]:
    snapshots = await business_service.get_business_vibe_snapshots(db, business_id)
    return [
        VibeSnapshotResponse.model_validate(s)
        for s in snapshots
    ]


@router.post("/vibe-snapshots/run/{business_id}")
async def run_snapshot(
    business_id: int,
    db: AsyncSession = Depends(get_db),
    models: MLRegistry = Depends(get_models)
):
    now = datetime.datetime.now(datetime.timezone.utc)
    snapshot = await business_service.run_vibe_snapshot_pipeline(
        db=db,
        business_id=business_id,
        models=models,
        snapshot_date=now
    )
    return snapshot


# -------------------------
# BUSINESS REVIEW ROUTES
# -------------------------
@router.get("/{business_id}/profile", response_model=BusinessResponse)
async def get_business_profile(
    business_id: int, db: Annotated[AsyncSession, Depends(get_db)]
) -> Business:
    return await business_service.get_business_profile(db, business_id)



# -------------------------
# GET SINGLE BUSINESS (GENERIC - MUST COME LAST)
# -------------------------
@router.get("/{business_id}", response_model=BusinessResponse)
async def get_business(
    business_id: int, db: Annotated[AsyncSession, Depends(get_db)]
) -> Business:
    business = await business_service.get_business_or_404(db, business_id)
    return business


# -------------------------
# UPDATE BUSINESS
# -------------------------
@router.patch("/{business_id}", response_model=BusinessResponse)
async def update_business(
    business_id: int,
    updated_business: BusinessUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Business:
    return await business_service.update_business(db, business_id, updated_business)


# -------------------------
# DELETE BUSINESS
# -------------------------
@router.delete("/{business_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_business(
    business_id: int, db: Annotated[AsyncSession, Depends(get_db)]
):
    await business_service.delete_business(db, business_id)

