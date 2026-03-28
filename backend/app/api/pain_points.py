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
            subreddit=_extract_subreddit(post.url),
            post_title=post.title,
            post_url=post.url,
            pain_point=pain_point.pain_point,
            category=pain_point.category,
            severity=pain_point.severity,
            score=pain_point.score,
            created_at=pain_point.created_at,
        )
        for pain_point, post in rows
    ]


def _extract_subreddit(url: str) -> str:
    marker = "/r/"
    if marker not in url:
        return "r/unknown"

    tail = url.split(marker, maxsplit=1)[1]
    subreddit_name = tail.split("/", maxsplit=1)[0].strip()
    if not subreddit_name:
        return "r/unknown"

    return f"r/{subreddit_name}"
