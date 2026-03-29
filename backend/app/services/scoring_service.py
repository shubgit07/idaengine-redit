from __future__ import annotations

import math


_SEVERITY_TO_SCORE = {
    "low": 0.33,
    "medium": 0.66,
    "high": 1.0,
}


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def compute_engagement_score(upvotes: int, num_comments: int) -> float:
    upvotes_value = max(0, int(upvotes))
    comments_value = max(0, int(num_comments))
    engagement_raw = math.log1p(upvotes_value) * 0.7 + math.log1p(comments_value) * 0.3
    normalized = engagement_raw / (engagement_raw + 1.0)
    return round(_clamp01(normalized), 4)


def compute_final_score(
    severity: str,
    emotional_intensity: float,
    willingness_to_pay: float,
    confidence: float,
    engagement_score: float,
) -> float:
    severity_score = _SEVERITY_TO_SCORE.get((severity or "").strip().lower(), _SEVERITY_TO_SCORE["medium"])
    emotional_score = _clamp01(emotional_intensity)
    willingness_score = _clamp01(willingness_to_pay)
    confidence_score = _clamp01(confidence)
    engagement = _clamp01(engagement_score)

    score = (
        0.30 * severity_score
        + 0.20 * emotional_score
        + 0.20 * willingness_score
        + 0.10 * confidence_score
        + 0.20 * engagement
    ) * 100.0

    return round(max(0.0, min(100.0, score)), 2)


def compute_score(
    severity: str,
    emotional_intensity: float,
    willingness_to_pay: float,
    confidence: float,
    upvotes: int,
    num_comments: int,
) -> float:
    engagement_score = compute_engagement_score(upvotes=upvotes, num_comments=num_comments)
    return compute_final_score(
        severity=severity,
        emotional_intensity=emotional_intensity,
        willingness_to_pay=willingness_to_pay,
        confidence=confidence,
        engagement_score=engagement_score,
    )