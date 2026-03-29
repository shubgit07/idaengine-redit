from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.reddit_post import RedditPostDB


class PainPointDB(Base):
    __tablename__ = "pain_points"
    __table_args__ = (
        CheckConstraint(
            "severity IN ('low', 'medium', 'high')",
            name="ck_pain_points_severity",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    reddit_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("reddit_posts.reddit_id"),
        index=True,
        nullable=False,
    )
    pain_point: Mapped[str] = mapped_column(String, nullable=False)
    pain_point_headline: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[str] = mapped_column(String, index=True, nullable=False)
    severity: Mapped[str] = mapped_column(String, nullable=False)
    emotional_intensity: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    willingness_to_pay: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    engagement_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    score_version: Mapped[str] = mapped_column(String, default="v1", nullable=False)
    score_reason: Mapped[str | None] = mapped_column(String, nullable=True)
    post: Mapped[RedditPostDB] = relationship(back_populates="pain_points")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
