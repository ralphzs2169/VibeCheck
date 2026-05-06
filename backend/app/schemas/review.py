from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

from backend.app.schemas.aspect_sentiment import AspectMiniResponse
from backend.app.schemas.user import UserMiniResponse

class ReviewBase(BaseModel):
    content: str = Field(..., max_length=500)

class ReviewCreate(ReviewBase):
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

    user: UserMiniResponse
    aspect_sentiments: list[AspectMiniResponse]

    model_config = ConfigDict(from_attributes=True)