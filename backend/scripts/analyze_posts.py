from __future__ import annotations

import argparse
import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy import select

from app.db.session import AsyncSessionLocal, init_db
from app.models.reddit_post import RedditPostDB
from app.schemas.reddit import RedditPost
from app.services.llm_service import analyze_post
from app.services.pain_point_persistence import save_pain_points

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BATCH_SIZE = 5


def _build_status_filter(reprocess_failed: bool) -> tuple[str, ...]:
    if reprocess_failed:
        return ("pending", "failed")
    return ("pending",)


def _to_schema_post(db_post: RedditPostDB) -> RedditPost:
    return RedditPost(
        id=db_post.reddit_id,
        title=db_post.title,
        post_body=db_post.post_body,
        subreddit=db_post.subreddit,
        upvotes=db_post.upvotes,
        num_comments=db_post.num_comments,
        created_utc=db_post.created_utc,
        url=db_post.url,
    )


async def _fetch_batch(statuses: tuple[str, ...]) -> list[RedditPostDB]:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(RedditPostDB)
            .where(RedditPostDB.analysis_status.in_(statuses))
            .order_by(RedditPostDB.id.asc())
            .limit(BATCH_SIZE)
        )
        return list(result.scalars().all())


async def _mark_processing(reddit_id: str) -> None:
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(RedditPostDB).where(RedditPostDB.reddit_id == reddit_id))
        post = result.scalar_one_or_none()
        if not post:
            return
        post.analysis_status = "processing"
        post.last_error = None
        await session.commit()


async def _mark_done(reddit_id: str) -> None:
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(RedditPostDB).where(RedditPostDB.reddit_id == reddit_id))
        post = result.scalar_one_or_none()
        if not post:
            return
        post.analysis_status = "done"
        post.analyzed_at = datetime.now(timezone.utc)
        post.last_error = None
        await session.commit()


async def _mark_failed(reddit_id: str, message: str) -> None:
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(RedditPostDB).where(RedditPostDB.reddit_id == reddit_id))
        post = result.scalar_one_or_none()
        if not post:
            return
        post.analysis_status = "failed"
        post.last_error = message[:2000]
        await session.commit()


async def run_analysis(reprocess_failed: bool = False) -> None:
    statuses = _build_status_filter(reprocess_failed=reprocess_failed)
    await init_db()

    logger.info("Starting analysis run for statuses=%s", statuses)
    total_done = 0
    total_failed = 0

    while True:
        batch = await _fetch_batch(statuses=statuses)
        if not batch:
            break

        logger.info("Processing batch of %d posts", len(batch))

        for db_post in batch:
            reddit_id = db_post.reddit_id
            await _mark_processing(reddit_id)

            try:
                analyzed_items = await analyze_post(_to_schema_post(db_post))
                if not analyzed_items:
                    raise ValueError("No valid JSON pain point extracted")

                async with AsyncSessionLocal() as session:
                    inserted = await save_pain_points(session, analyzed_items)

                if inserted == 0:
                    logger.info("No new pain point row for reddit_id=%s (duplicate or unchanged)", reddit_id)

                await _mark_done(reddit_id)
                total_done += 1
            except Exception as exc:
                logger.exception("Failed analysis for reddit_id=%s", reddit_id)
                await _mark_failed(reddit_id, str(exc))
                total_failed += 1

    logger.info("Analysis complete. done=%d failed=%d", total_done, total_failed)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze pending Reddit posts with LLM")
    parser.add_argument(
        "--reprocess-failed",
        action="store_true",
        help="Also include failed posts in this run.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    asyncio.run(run_analysis(reprocess_failed=args.reprocess_failed))