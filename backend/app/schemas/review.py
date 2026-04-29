from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

class ReviewBase(BaseModel):
    title: str = Field(..., max_length=100)
    content: str = Field(..., max_length=500)
    sentiment_score: float = Field(..., ge=-1, le=1)
    sentiment_label: str = Field(..., max_length=20)

class ReviewCreate(ReviewBase):
    pass

class ReviewUpdate(ReviewBase):
    pass

class ReviewResponse(ReviewBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)