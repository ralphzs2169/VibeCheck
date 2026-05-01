from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.core.database import Base

if TYPE_CHECKING:
    from backend.app.models.review import Review


class AspectSentiment(Base):
    __tablename__ = "aspect_sentiments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    sentence: Mapped[str] = mapped_column(Text, nullable=False)
    aspect: Mapped[str] = mapped_column(String(50), nullable=False)

    sentiment_label: Mapped[str] = mapped_column(String(20), nullable=False)
    sentiment_score: Mapped[float] = mapped_column(Float, nullable=False)
    
    # This represents the confidence of the aspect detection 
    # (how closely the sentence matched the aspect)
    aspect_confidence: Mapped[float] = mapped_column(Float, nullable=False) 

    # This can be used to filter out low-confidence predictions in the future if needed
    sentiment_confidence: Mapped[float] = mapped_column(Float, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC)
    )

    review_id: Mapped[int] = mapped_column(
        ForeignKey("reviews.id"),
        nullable=False,
        index=True
    )

    # Establish relationship with Review (the review this aspect sentiment is associated with)
    review: Mapped[Review] = relationship(
        "Review",
        back_populates="aspect_sentiments"
    )