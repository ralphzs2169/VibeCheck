from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.schemas.user import UserCreate, UserResponse, UserUpdate
import backend.app.services.user_service as user_service

router = APIRouter()


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_user(user: UserCreate, db: Annotated[AsyncSession, Depends(get_db)]):
    return await user_service.create_user(db, user)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    return await user_service.get_user_or_404(db, user_id)


@router.get("", response_model=list[UserResponse])
async def get_all_users(db: Annotated[AsyncSession, Depends(get_db)]):
    return await user_service.get_all_users(db)


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    updated_user: UserUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await user_service.update_user(db, user_id, updated_user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    return await user_service.delete_user(db, user_id)
