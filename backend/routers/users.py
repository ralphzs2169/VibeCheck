from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.schemas.user import UserCreate, UserResponse, UserUpdate

from backend.app.models.user import User
from backend.app.core.database import get_db

from backend.services.user_service import get_user_or_404

router = APIRouter()

# Create User
@router.post(
    "", 
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_user(user: UserCreate, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
        select(User).where(User.username == user.username),
    )
    existing_user = result.scalars().first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists",
        )

    new_user = User(
        username=user.username,
        firstname=user.firstname,
        lastname=user.lastname
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user


# Get User by ID
@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    user = await get_user_or_404(db, user_id)
    return user


# Get all Users
@router.get("", response_model=list[UserResponse])
async def get_users(db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
        select(User).options(selectinload(User.reviews))
    )
    users = result.scalars().all()
    return users


# Update User
@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    updated_user: UserUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    user = await get_user_or_404(db, user_id)

    update_data = updated_user.model_dump(exclude_unset=True)

    # Check username conflict ONLY if username is being updated
    if "username" in update_data and update_data["username"] != user.username:
        result = await db.execute(
            select(User).where(User.username == update_data["username"]),
        )
        existing_user = result.scalars().first()

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists",
            )

    # Apply updates safely
    for field, value in update_data.items():
        setattr(user, field, value)

    await db.commit()
    await db.refresh(user)

    return user


# Delete User
@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    user = await get_user_or_404(db, user_id)

    await db.delete(user)
    await db.commit()