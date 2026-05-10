from typing import Annotated

import os
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

import backend.app.services.auth_service as auth_service
import backend.app.services.user_service as user_service
import backend.app.services.business_service as business_service
from backend.app.core.database import get_db
from backend.app.core.constants import UPLOADS_DIR
from backend.app.models.user import User
from backend.app.schemas.business import BusinessCreate
from backend.app.schemas.user import (
    TokenResponse,
    UserCreate,
    UserLogin,
    UserMiniResponse,
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

    user_obj = await user_service.get_user_by_username(db, credentials.username)

    business_id = user_obj.business.id if user_obj.business else None

    return {
        "access_token": result,
        "token_type": "bearer",
        "user": {
            **UserMiniResponse.model_validate(user_obj).model_dump(),
            "business_id": business_id
        }
    }


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user: UserCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await user_service.create_user(db, user)


@router.get("/me", response_model=UserResponse)
async def read_current_user(
    current_user: User = Depends(auth_service.get_authenticated_user),
):
    return current_user


@router.post("/owner/register")
# Using Form and File parameters instead of a Pydantic model for multipart/form-data handling
async def register_owner(
    username: str = Form(...),
    firstname: str | None = Form(None),
    lastname: str | None = Form(None),
    password: str = Form(...),
    business_name: str = Form(...),
    location: str = Form(...),
    short_description: str = Form(...),
    image: UploadFile | None = File(None),
    db: AsyncSession = Depends(get_db)
):
    user_payload = UserCreate(
        username=username,
        firstname=firstname,
        lastname=lastname,
        role="owner",
        password=password,
    )

    image_path = None
    # Handle file upload if an image is provided
    if image:
        UPLOADS_DIR.mkdir(exist_ok=True)
        _, ext = os.path.splitext(image.filename or "")
        ext = ext.lower() if ext else ".png"
        filename = f"{uuid.uuid4().hex}{ext}"
        file_path = UPLOADS_DIR / filename

        contents = await image.read()
        with open(file_path, "wb") as f:
            f.write(contents)

        image_path = f"/uploads/{filename}"

    user = await user_service.create_user(db, user_payload)

    business_payload = {
        "name": business_name,
        "location": location,
        "short_description": short_description,
        "image_path": image_path,
    }

    business = await business_service.create_business(
        db,
        BusinessCreate(**business_payload),
        owner_id=user.id
    )

    return {
        "user": user,
        "business": business
    }


@router.post("/logout")
async def logout(
    current_user = Depends(auth_service.get_authenticated_user),
    db: AsyncSession = Depends(get_db),
):
    await auth_service.logout_user(db, current_user)

    return {
        "message": "Successfully logged out"
    }