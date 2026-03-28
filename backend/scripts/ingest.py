from __future__ import annotations

import asyncio
import logging

from app.db.session import AsyncSessionLocal, init_db
from app.schemas.reddit import RedditPost
from app.services.llm_service import extract_pain_points
from app.services.pain_point_persistence import save_pain_points
from app.services.reddit_persistence import save_posts
from app.services.reddit_service import RedditService, RedditServiceError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TARGET_SUBREDDITS = ["Entrepreneur", "startups", "SaaS", "smallbusiness"]


async def run_ingestion() -> None:
	"""Run the Reddit ingestion step and emit top posts for downstream processing.

	This currently logs fetched post data for operational visibility and will later
	feed persisted records once database integration is introduced.
	"""
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
			"Title: %s | Score: %s | Comments: %s | URL: %s",
			post.title,
			post.score,
			post.num_comments,
			post.url,
		)

	async with AsyncSessionLocal() as session:
		inserted = await save_posts(session, posts)

	logger.info("Inserted %d new posts into DB", inserted)
	pain_points = await extract_pain_points(posts)
	logger.info("Extracted %d pain points", len(pain_points))
	async with AsyncSessionLocal() as session:
		inserted_pp = await save_pain_points(session, pain_points)
	logger.info("Inserted %d pain points", inserted_pp)
	if pain_points:
		logger.info("Sample pain point: %s", pain_points[0])
		if len(pain_points) > 1:
			logger.info("Sample pain point: %s", pain_points[1])

	logger.info("Ingestion completed. Fetched %d posts.", len(posts))


if __name__ == "__main__":
	asyncio.run(run_ingestion())
