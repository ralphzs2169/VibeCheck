from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING

from backend.app.core.database import Base

if TYPE_CHECKING:
    from backend.app.models.business import Business


class VibeSnapshot(Base):
    __tablename__ = "vibe_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    vibe_score: Mapped[float] = mapped_column(Float, nullable=False)
    vibe_label: Mapped[str] = mapped_column(String, nullable=False)

    review_count: Mapped[int] = mapped_column(Integer, nullable=False)

    positive_count: Mapped[int] = mapped_column(Integer, nullable=False)
    mixed_count: Mapped[int] = mapped_column(Integer, nullable=False)
    negative_count: Mapped[int] = mapped_column(Integer, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    snapshot_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True
    )

    business_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("businesses.id"), nullable=False, index=True
    )

    # Establish relationship with Business (the business this vibe snapshot belongs to)
    business: Mapped["Business"] = relationship(
        "Business", back_populates="vibe_snapshots"
    )
