from __future__ import annotations

from typing import Any

from sqlalchemy import select, tuple_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.pain_point import PainPointDB


async def save_pain_points(
    session: AsyncSession,
    items: list[dict],
) -> int:
    candidate_rows: list[tuple[str, str, str, str, float | None]] = []
    seen_pairs: set[tuple[str, str]] = set()

    for item in items:
        payload: dict[str, Any] = item
        reddit_id = item.get("reddit_id")
        pain_point = item.get("pain_point")
        category = item.get("category")
        severity = item.get("severity")
        score = payload.get("score")

        if not isinstance(reddit_id, str) or not reddit_id.strip():
            continue
        if not isinstance(pain_point, str) or not pain_point.strip():
            continue
        if not isinstance(category, str) or not category.strip():
            continue
        if not isinstance(severity, str) or severity not in {"low", "medium", "high"}:
            continue
        if score is not None and not isinstance(score, (int, float)):
            continue

        key = (reddit_id.strip(), pain_point.strip())
        if key in seen_pairs:
            continue

        candidate_rows.append(
            (key[0], key[1], category.strip(), severity, float(score) if score is not None else None)
        )
        seen_pairs.add(key)

    if not candidate_rows:
        await session.commit()
        return 0

    candidate_pairs = [(row[0], row[1]) for row in candidate_rows]

    existing_result = await session.execute(
        select(PainPointDB.reddit_id, PainPointDB.pain_point).where(
            tuple_(PainPointDB.reddit_id, PainPointDB.pain_point).in_(candidate_pairs)
        )
    )
    existing_pairs = {(reddit_id, pain_point) for reddit_id, pain_point in existing_result.all()}

    new_rows = [
        PainPointDB(
            reddit_id=row[0],
            pain_point=row[1],
            category=row[2],
            severity=row[3],
            score=row[4],
        )
        for row in candidate_rows
        if (row[0], row[1]) not in existing_pairs
    ]

    if new_rows:
        session.add_all(new_rows)

    await session.commit()
    return len(new_rows)
