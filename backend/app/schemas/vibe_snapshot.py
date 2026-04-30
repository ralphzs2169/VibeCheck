from datetime import datetime
from pydantic import BaseModel, ConfigDict


class VibeSnapshotBase(BaseModel):
    business_id: int
    avg_score: float
    vibe_label: str
    review_count: int

    positive_count: int
    mixed_count: int
    negative_count: int


class VibeSnapshotResponse(VibeSnapshotBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)