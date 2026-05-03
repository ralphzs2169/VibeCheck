import hashlib
import hmac
import secrets
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
import backend.app.services.user_service as user_service


security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials = Depends(security),
    db: AsyncSession = Depends(get_db),
):
    if not credentials:
        return None

    token = credentials.credentials
    user = await user_service.get_user_by_token(db, token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_authenticated_user(current_user=Depends(get_current_user)):
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return current_user
