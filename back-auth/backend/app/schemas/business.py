from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

from backend.app.schemas.review import ReviewResponse

class BusinessBase(BaseModel):
    name: str = Field(..., max_length=100)
    location: str = Field(..., max_length=100)
    short_description: str = Field(..., max_length=255)
    image_path: str | None = Field(None, max_length=255)

class BusinessCreate(BusinessBase):
    pass

class BusinessUpdate(BusinessBase):
    name: str | None = Field(None, max_length=100)
    location: str | None = Field(None, max_length=100)
    short_description: str | None = Field(None, max_length=255)
    image_path: str | None = Field(None, max_length=255)

class BusinessResponse(BusinessBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class BusinessWithReviewsResponse(BusinessResponse):
    reviews: list[ReviewResponse] = Field(default_factory=list)