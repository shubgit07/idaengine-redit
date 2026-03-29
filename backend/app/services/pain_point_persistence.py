from __future__ import annotations

from typing import Any

from sqlalchemy import select, tuple_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.pain_point import PainPointDB


async def save_pain_points(
    session: AsyncSession,
    items: list[dict],
) -> int:
    candidate_rows: list[
        tuple[
            str,
            str,
            str | None,
            str,
            str,
            float | None,
            float | None,
            float | None,
            float | None,
            float | None,
            str | None,
            str | None,
        ]
    ] = []
    seen_pairs: set[tuple[str, str]] = set()

    for item in items:
        payload: dict[str, Any] = item
        reddit_id = item.get("reddit_id")
        pain_point = item.get("pain_point")
        pain_point_headline = payload.get("pain_point_headline")
        category = item.get("category")
        severity = item.get("severity")
        emotional_intensity = payload.get("emotional_intensity")
        willingness_to_pay = payload.get("willingness_to_pay")
        confidence = payload.get("confidence")
        engagement_score = payload.get("engagement_score")
        score = payload.get("score")
        score_version = payload.get("score_version")
        score_reason = payload.get("score_reason")

        if not isinstance(reddit_id, str) or not reddit_id.strip():
            continue
        if not isinstance(pain_point, str) or not pain_point.strip():
            continue
        if not isinstance(category, str) or not category.strip():
            continue
        if not isinstance(severity, str) or severity not in {"low", "medium", "high"}:
            continue
        if not isinstance(pain_point_headline, str) or not pain_point_headline.strip():
            continue
        if not isinstance(emotional_intensity, (int, float)):
            continue
        if not isinstance(willingness_to_pay, (int, float)):
            continue
        if not isinstance(confidence, (int, float)):
            continue
        if not isinstance(engagement_score, (int, float)):
            continue
        if not isinstance(score, (int, float)):
            continue
        if not isinstance(score_version, str) or not score_version.strip():
            continue
        if score_reason is not None and not isinstance(score_reason, str):
            continue

        key = (reddit_id.strip(), pain_point.strip())
        if key in seen_pairs:
            continue

        candidate_rows.append(
            (
                key[0],
                key[1],
                pain_point_headline.strip(),
                category.strip(),
                severity,
                float(emotional_intensity),
                float(willingness_to_pay),
                float(confidence),
                float(engagement_score),
                float(score),
                score_version.strip(),
                score_reason.strip() if isinstance(score_reason, str) and score_reason.strip() else None,
            )
        )
        seen_pairs.add(key)

    if not candidate_rows:
        await session.commit()
        return 0

    candidate_pairs = [(row[0], row[1]) for row in candidate_rows]

    existing_result = await session.execute(
        select(PainPointDB).where(
            tuple_(PainPointDB.reddit_id, PainPointDB.pain_point).in_(candidate_pairs)
        )
    )
    existing_rows = {
        (row.reddit_id, row.pain_point): row
        for row in existing_result.scalars().all()
    }

    new_rows = [
        PainPointDB(
            reddit_id=row[0],
            pain_point=row[1],
            pain_point_headline=row[2],
            category=row[3],
            severity=row[4],
            emotional_intensity=row[5],
            willingness_to_pay=row[6],
            confidence=row[7],
            engagement_score=row[8],
            score=row[9],
            score_version=row[10],
            score_reason=row[11],
        )
        for row in candidate_rows
        if (row[0], row[1]) not in existing_rows
    ]

    updated_count = 0
    for row in candidate_rows:
        key = (row[0], row[1])
        existing = existing_rows.get(key)
        if not existing:
            continue

        existing.pain_point_headline = row[2] if row[2] is not None else existing.pain_point_headline
        existing.category = row[3]
        existing.severity = row[4]
        existing.emotional_intensity = row[5] if row[5] is not None else existing.emotional_intensity
        existing.willingness_to_pay = row[6] if row[6] is not None else existing.willingness_to_pay
        existing.confidence = row[7] if row[7] is not None else existing.confidence
        existing.engagement_score = row[8] if row[8] is not None else existing.engagement_score
        existing.score = row[9] if row[9] is not None else existing.score
        existing.score_version = row[10] if row[10] is not None else existing.score_version
        existing.score_reason = row[11]
        updated_count += 1

    if new_rows:
        session.add_all(new_rows)

    await session.commit()
    return len(new_rows) + updated_count
