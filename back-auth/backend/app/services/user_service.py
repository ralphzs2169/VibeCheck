import hashlib
import hmac
import secrets

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

DEFAULT_ROLE = "reviewer"

from backend.app.models.user import User
from backend.app.schemas.user import UserCreate, UserUpdate

PASSWORD_HASH_ITERATIONS = 100_000


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        PASSWORD_HASH_ITERATIONS,
    )
    return f"{salt}${key.hex()}"


def verify_password(password: str, hashed_password: str) -> bool:
    try:
        salt, stored_key = hashed_password.split("$", 1)
    except ValueError:
        return False

    key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        PASSWORD_HASH_ITERATIONS,
    )
    return hmac.compare_digest(key.hex(), stored_key)


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
        lastname=user.lastname,
        role=user.role or DEFAULT_ROLE,
        hashed_password=hash_password(user.password),
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


async def get_user_by_username(db: AsyncSession, username: str) -> User | None:
    result = await db.execute(select(User).where(User.username == username))
    return result.scalars().first()


async def get_user_by_token(db: AsyncSession, token: str) -> User | None:
    result = await db.execute(select(User).where(User.token == token))
    return result.scalars().first()


async def authenticate_user(
    db: AsyncSession,
    username: str,
    password: str,
) -> User | None:
    user = await get_user_by_username(db, username)
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user


async def create_access_token(db: AsyncSession, user: User) -> str:
    token = secrets.token_urlsafe(32)
    user.token = token
    await db.commit()
    await db.refresh(user)
    return token


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

    if "password" in update_data:
        user.hashed_password = hash_password(update_data.pop("password"))

    for field, value in update_data.items():
        setattr(user, field, value)

    await db.commit()
    await db.refresh(user)

    return user


async def delete_user(db: AsyncSession, user_id: int) -> None:
    user = await get_user_or_404(db, user_id)

    await db.delete(user)
    await db.commit()