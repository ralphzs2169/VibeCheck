from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

class UserBase(BaseModel):
    username: str = Field(..., max_length=50)
    firstname: str = Field(..., max_length=20)
    lastname: str = Field(..., max_length=20)


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=128)


class UserUpdate(BaseModel):
    username: str | None = Field(None, max_length=50)
    firstname: str | None = Field(None, max_length=20)
    lastname: str | None = Field(None, max_length=20)
    password: str | None = Field(None, min_length=8, max_length=128)


class UserLogin(BaseModel):
    username: str = Field(..., max_length=50)
    password: str = Field(..., min_length=8, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


class UserResponse(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

