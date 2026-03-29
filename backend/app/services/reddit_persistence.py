from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.reddit_post import RedditPostDB
from app.schemas.reddit import RedditPost


async def save_posts(
    session: AsyncSession,
    posts: list[RedditPost],
) -> int:
    """Persist new Reddit posts and return the number of inserted rows."""
    if not posts:
        await session.commit()
        return 0

    post_ids = [post.id for post in posts]
    existing_result = await session.execute(
        select(RedditPostDB.reddit_id).where(RedditPostDB.reddit_id.in_(post_ids))
    )
    existing_ids = set(existing_result.scalars().all())

    new_rows = [
        RedditPostDB(
            reddit_id=post.id,
            subreddit=post.subreddit,
            title=post.title,
            post_body=post.post_body,
            upvotes=post.upvotes,
            num_comments=post.num_comments,
            url=post.url,
            created_utc=post.created_utc,
            analysis_status="pending",
        )
        for post in posts
        if post.id not in existing_ids
    ]

    if new_rows:
        session.add_all(new_rows)

    await session.commit()
    return len(new_rows)
