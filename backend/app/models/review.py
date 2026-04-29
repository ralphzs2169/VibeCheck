from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.core.database import Base

class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    sentiment_score: Mapped[float] = mapped_column(nullable=False)
    sentiment_label: Mapped[str] = mapped_column(String(20), nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    # Establish relationship with User (author of the review)
    user: Mapped["User"] = relationship("User", back_populates="reviews")

  