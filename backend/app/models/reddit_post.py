from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.pain_point import PainPointDB


class RedditPostDB(Base):
    __tablename__ = "reddit_posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    reddit_id: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    subreddit: Mapped[str] = mapped_column(String, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    post_body: Mapped[str] = mapped_column(String, nullable=False, default="")
    upvotes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    num_comments: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    url: Mapped[str] = mapped_column(String, nullable=False)
    created_utc: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    analysis_status: Mapped[str] = mapped_column(String, nullable=False, default="pending", index=True)
    analyzed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error: Mapped[str | None] = mapped_column(String, nullable=True)
    inserted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    pain_points: Mapped[list[PainPointDB]] = relationship(back_populates="post")
