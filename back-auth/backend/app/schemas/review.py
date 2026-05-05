from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

class ReviewBase(BaseModel):
    content: str = Field(..., max_length=500)

class ReviewCreate(ReviewBase):
    user_id: int | None = Field(None, gt=0)
    business_id: int = Field(..., gt=0)

class ReviewUpdate(ReviewBase):
    content: str | None = Field(None, max_length=500)

class ReviewResponse(ReviewBase):
    id: int

    sentiment_score: float
    sentiment_label: str 

    created_at: datetime
    updated_at: datetime

    user_id: int
    business_id: int

    model_config = ConfigDict(from_attributes=True)