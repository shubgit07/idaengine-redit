from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PainPoint(BaseModel):
    id: int
    reddit_id: str
    subreddit: str
    post_title: str
    post_url: str
    pain_point: str
    category: str
    severity: str
    score: float | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
