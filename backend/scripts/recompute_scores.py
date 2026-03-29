from __future__ import annotations

import asyncio
import logging

from sqlalchemy import select

from app.db.session import AsyncSessionLocal, init_db
from app.models.pain_point import PainPointDB
from app.models.reddit_post import RedditPostDB
from app.services.scoring_service import compute_engagement_score, compute_final_score

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def recompute_scores() -> None:
    """Recompute scores from persisted fields without calling the LLM."""
    await init_db()

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(PainPointDB, RedditPostDB).join(RedditPostDB, PainPointDB.reddit_id == RedditPostDB.reddit_id)
        )
        rows = result.all()

        updated = 0
        for pain_point, post in rows:
            upvotes = int(max(0, post.upvotes))
            num_comments = int(max(0, post.num_comments))
            engagement_score = compute_engagement_score(upvotes=upvotes, num_comments=num_comments)
            pain_point.engagement_score = engagement_score
            pain_point.score = compute_final_score(
                severity=pain_point.severity,
                emotional_intensity=pain_point.emotional_intensity,
                willingness_to_pay=pain_point.willingness_to_pay,
                confidence=pain_point.confidence,
                engagement_score=engagement_score,
            )
            pain_point.score_version = "v3"
            updated += 1

        await session.commit()

    logger.info("Recomputed scores for %d pain points", updated)


if __name__ == "__main__":
    asyncio.run(recompute_scores())
