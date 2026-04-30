from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from backend.app.models.user import User
from backend.app.schemas.user import UserCreate, UserUpdate


async def create_user(db: AsyncSession, user: UserCreate) -> User:
    result = await db.execute(
        select(User).where(User.username == user.username)
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


async def get_user_or_404(db: AsyncSession, user_id: int) -> User:
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return user


async def get_all_users(db: AsyncSession) -> list[User]:
    result = await db.execute(
        select(User)
    )
    return result.scalars().all()


async def update_user(
    db: AsyncSession,
    user_id: int,
    updated_user: UserUpdate
) -> User:

    user = await get_user_or_404(db, user_id)

    update_data = updated_user.model_dump(exclude_unset=True)

    if "username" in update_data and update_data["username"] != user.username:
        result = await db.execute(
            select(User).where(User.username == update_data["username"])
        )
        existing_user = result.scalars().first()

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists",
            )

    for field, value in update_data.items():
        setattr(user, field, value)

    await db.commit()
    await db.refresh(user)

    return user


async def delete_user(db: AsyncSession, user_id: int) -> None:
    user = await get_user_or_404(db, user_id)

    await db.delete(user)
    await db.commit()