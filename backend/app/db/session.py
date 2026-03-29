from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncSession, async_sessionmaker, create_async_engine

from app.db.base import Base
from app import models as _models  # noqa: F401

DATABASE_URL = "sqlite+aiosqlite:///./app.db"

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await _ensure_reddit_posts_columns(conn)
        await _ensure_pain_points_columns(conn)


async def _ensure_reddit_posts_columns(conn: AsyncConnection) -> None:
    result = await conn.execute(text("PRAGMA table_info(reddit_posts)"))
    columns = {str(row[1]) for row in result.fetchall()}

    if "analysis_status" not in columns:
        await conn.execute(
            text("ALTER TABLE reddit_posts ADD COLUMN analysis_status VARCHAR NOT NULL DEFAULT 'pending'")
        )
    if "analyzed_at" not in columns:
        await conn.execute(text("ALTER TABLE reddit_posts ADD COLUMN analyzed_at DATETIME"))
    if "last_error" not in columns:
        await conn.execute(text("ALTER TABLE reddit_posts ADD COLUMN last_error TEXT"))

    await conn.execute(
        text(
            "UPDATE reddit_posts "
            "SET analysis_status = 'pending' "
            "WHERE analysis_status IS NULL OR TRIM(analysis_status) = ''"
        )
    )
    await conn.execute(
        text("CREATE INDEX IF NOT EXISTS ix_reddit_posts_analysis_status ON reddit_posts (analysis_status)")
    )


async def _ensure_pain_points_columns(conn: AsyncConnection) -> None:
    result = await conn.execute(text("PRAGMA table_info(pain_points)"))
    columns = {str(row[1]) for row in result.fetchall()}

    if "engagement_score" not in columns:
        await conn.execute(text("ALTER TABLE pain_points ADD COLUMN engagement_score FLOAT NOT NULL DEFAULT 0"))
