from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

import backend.app.services.auth_service as auth_service
from backend.app.core.database import get_db
from backend.app.models.user import User
from backend.app.schemas.user import (
    TokenResponse,
    UserLogin,
    UserResponse,
)

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: UserLogin,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await auth_service.login_user(
        db,
        credentials.username,
        credentials.password
    )

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return {
        "access_token": result,
        "token_type": "bearer"
    }


@router.get("/me", response_model=UserResponse)
async def read_current_user(
    current_user: User = Depends(auth_service.get_authenticated_user),
):
    print("ROUTER HIT")
    return current_user


@router.post("/logout")
async def logout(
    current_user = Depends(auth_service.get_authenticated_user),
    db: AsyncSession = Depends(get_db),
):
    await auth_service.logout_user(db, current_user)

    return {
        "message": "Successfully logged out"
    }