from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.core.database import Base

if TYPE_CHECKING:
    from backend.app.models.user import User
    from backend.app.models.review import Review
    from backend.app.models.vibe_snapshot import VibeSnapshot

class Business(Base):
    __tablename__ = "businesses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    location: Mapped[str] = mapped_column(String(100), nullable=False)
    short_description: Mapped[str] = mapped_column(String(255), nullable=False)
    image_path: Mapped[str | None] = mapped_column(String(255), nullable=True)

    owner_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    owner: Mapped["User | None"] = relationship(
        "User", back_populates="businesses"
    )
    reviews: Mapped[list["Review"]] = relationship(
        "Review", back_populates="business", cascade="all, delete-orphan"
    )
    vibe_snapshots: Mapped[list["VibeSnapshot"]] = relationship(
        "VibeSnapshot", back_populates="business", cascade="all, delete-orphan"
    )