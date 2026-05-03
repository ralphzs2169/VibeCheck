from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

import backend.app.services.user_service as user_service
import backend.app.services.business_service as business_service
from backend.app.core.auth import get_authenticated_user
from backend.app.core.database import get_db
from backend.app.schemas.user import (
    TokenResponse,
    UserCreate,
    UserLogin,
    UserResponse,
    UserUpdate,
)
from backend.app.schemas.business import BusinessResponse

router = APIRouter()


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_user(user: UserCreate, db: Annotated[AsyncSession, Depends(get_db)]):
    return await user_service.create_user(db, user)


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: UserLogin,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    user = await user_service.authenticate_user(
        db, credentials.username, credentials.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = await user_service.create_access_token(db, user)
    return {"access_token": token, "token_type": "bearer", "role": user.role, "user_id": user.id}


@router.get("/me", response_model=UserResponse)
async def read_current_user(
    current_user=Depends(get_authenticated_user),
):
    return current_user


@router.get("/me/businesses", response_model=list[BusinessResponse])
async def get_my_businesses(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user=Depends(get_authenticated_user),
):
    if current_user.role != "merchant":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only merchants have businesses")
    return await business_service.get_businesses_by_owner(db, current_user.id)


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