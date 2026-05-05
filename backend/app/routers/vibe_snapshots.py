from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.core.database import get_db
from backend.app.models.vibe_snapshot import VibeSnapshot
from backend.app.schemas.vibe_snapshot import VibeSnapshotResponse
from backend.app.services import vibe_snapshot_service

router = APIRouter()

@router.get("", response_model=list[VibeSnapshotResponse])
async def get_vibe_snapshots(db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
        select(VibeSnapshot).options(selectinload(VibeSnapshot.business))
    )
    vibe_snapshots = result.scalars().all()
    return vibe_snapshots


@router.get("/latest/{snapshot_id}", response_model=VibeSnapshotResponse)
async def get_latest_vibe_snapshot(snapshot_id: int, db: Annotated[AsyncSession, Depends(get_db)]): 
    return await vibe_snapshot_service.get_vibe_snapshot_or_404(db, snapshot_id)