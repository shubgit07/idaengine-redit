from __future__ import annotations

import asyncio
import logging

from app.db.session import AsyncSessionLocal, init_db
from app.schemas.reddit import RedditPost
from app.services.reddit_persistence import save_posts
from app.services.reddit_service import RedditService, RedditServiceError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TARGET_SUBREDDITS = ["Entrepreneur", "startups", "SaaS", "smallbusiness"]


async def run_ingestion() -> None:
	"""Fetch Reddit posts and persist them for downstream analysis."""
	logger.info("Starting Reddit ingestion...")
	await init_db()
	try:
		async with RedditService() as service:
			posts: list[RedditPost] = await service.fetch_top_posts_for_subreddits(
				subreddits=TARGET_SUBREDDITS,
				limit=5,
			)
	except RedditServiceError as exc:
		logger.error("Ingestion failed while fetching Reddit posts: %s", exc)
		return
	except Exception:
		logger.exception("Unexpected failure during Reddit ingestion")
		return

	if not posts:
		logger.info("No posts found.")
		return

	for post in posts:
		logger.info(
			"Title: %s | Upvotes: %s | Comments: %s | URL: %s",
			post.title,
			post.upvotes,
			post.num_comments,
			post.url,
		)

	async with AsyncSessionLocal() as session:
		inserted = await save_posts(session, posts)

	logger.info("Inserted %d new posts into DB", inserted)
	logger.info(
		"Ingestion completed. Fetched %d posts; new posts are marked pending for analysis.",
		len(posts),
	)


if __name__ == "__main__":
	asyncio.run(run_ingestion())
