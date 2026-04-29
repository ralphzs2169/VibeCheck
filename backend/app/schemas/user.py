from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

class UserBase(BaseModel):
    username: str = Field(..., max_length=50)
    firstname: str = Field(..., max_length=20)
    lastname: str = Field(..., max_length=20)


class UserCreate(UserBase):
    pass

class UserUpdate(BaseModel):
    username: str | None = Field(None, max_length=50)
    firstname: str | None = Field(None, max_length=20)
    lastname: str | None = Field(None, max_length=20)

class UserResponse(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

