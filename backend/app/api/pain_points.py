from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.models.pain_point import PainPointDB
from app.models.reddit_post import RedditPostDB
from app.schemas.pain_point import PainPoint

router = APIRouter()


@router.get("/", response_model=list[PainPoint])
async def list_pain_points(session: AsyncSession = Depends(get_session)) -> list[PainPoint]:
    result = await session.execute(
        select(PainPointDB, RedditPostDB)
        .join(RedditPostDB, PainPointDB.reddit_id == RedditPostDB.reddit_id)
        .order_by(PainPointDB.created_at.desc())
    )

    rows = result.all()
    return [
        PainPoint(
            id=pain_point.id,
            reddit_id=pain_point.reddit_id,
            subreddit=post.subreddit,
            post_title=post.title,
            post_url=post.url,
            pain_point=pain_point.pain_point,
            pain_point_headline=pain_point.pain_point_headline,
            category=pain_point.category,
            severity=pain_point.severity,
            emotional_intensity=pain_point.emotional_intensity,
            willingness_to_pay=pain_point.willingness_to_pay,
            confidence=pain_point.confidence,
            engagement_score=pain_point.engagement_score,
            score=pain_point.score,
            score_version=pain_point.score_version,
            score_reason=pain_point.score_reason,
            created_at=pain_point.created_at,
        )
        for pain_point, post in rows
    ]
