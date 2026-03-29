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
    pain_point_headline: str
    category: str
    severity: str
    emotional_intensity: float
    willingness_to_pay: float
    confidence: float
    engagement_score: float
    score: float
    score_version: str
    score_reason: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
