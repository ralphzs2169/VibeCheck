from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.core.database import Base

if TYPE_CHECKING:
    from backend.app.models.user import User
    from backend.app.models.business import Business
    from backend.app.models.aspect_sentiment import AspectSentiment


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    sentiment_score: Mapped[float] = mapped_column(nullable=True)
    sentiment_label: Mapped[str] = mapped_column(String(20), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    business_id: Mapped[int] = mapped_column(
        ForeignKey("businesses.id"), nullable=False
    )

    # Establish relationship with User (author of the review)
    user: Mapped["User"] = relationship("User", back_populates="reviews")

    # Establish relationship with Business (the business being reviewed)
    business: Mapped["Business"] = relationship("Business", back_populates="reviews")

    # Establish relationship with AspectSentiment (aspect sentiments associated with the review)
    aspect_sentiments: Mapped[list["AspectSentiment"]] = relationship(
        "AspectSentiment", back_populates="review", cascade="all, delete-orphan"
    )
