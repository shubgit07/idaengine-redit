from __future__ import annotations

import asyncio
import json
import logging
import os
import re
from typing import Any

import httpx
from dotenv import load_dotenv

from app.core.retry import async_retry
from app.schemas.reddit import RedditPost
from app.services.chunking_service import chunk_text
from app.services.scoring_service import compute_engagement_score, compute_final_score

logger = logging.getLogger(__name__)

load_dotenv()

SYSTEM_PROMPT = "You are a startup analyst extracting REAL user pain points from Reddit posts."

_SEVERITY_RANK = {
    "low": 1,
    "medium": 2,
    "high": 3,
}

_STOPWORDS = {
    "the",
    "a",
    "an",
    "and",
    "or",
    "to",
    "of",
    "for",
    "in",
    "on",
    "with",
    "is",
    "are",
    "was",
    "were",
    "be",
    "been",
    "being",
    "it",
    "this",
    "that",
    "my",
    "our",
    "i",
    "we",
    "they",
    "you",
}


def _build_chat_completions_url(base_url: str) -> str:
    normalized = (base_url or "").strip().rstrip("/")
    if not normalized:
        normalized = "https://api.openai.com/v1"
    return f"{normalized}/chat/completions"


def _extract_message_content(data: dict[str, Any]) -> str:
    choices = data.get("choices", [])
    if not choices:
        return ""

    message = choices[0].get("message", {})
    content = message.get("content", "")

    if isinstance(content, str):
        return content

    if isinstance(content, list):
        text_parts: list[str] = []
        for part in content:
            if isinstance(part, dict) and part.get("type") == "text":
                text_parts.append(str(part.get("text", "")))
        return "".join(text_parts)

    return str(content)


def _to_unit_interval(value: Any, default: float = 0.0) -> float:
    if not isinstance(value, (int, float)):
        return default
    return float(max(0.0, min(1.0, value)))


def _normalize_severity(value: Any) -> str:
    if isinstance(value, str) and value.strip().lower() in {"low", "medium", "high"}:
        return value.strip().lower()
    return "medium"


def _extract_json_payload(raw: str) -> list[dict[str, Any]]:
    if not raw:
        return []

    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.startswith("json"):
            cleaned = cleaned[4:].strip()

    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, list):
            return [item for item in parsed if isinstance(item, dict)]
        if isinstance(parsed, dict):
            if isinstance(parsed.get("pain_points"), list):
                return [item for item in parsed["pain_points"] if isinstance(item, dict)]
            return [parsed]
    except json.JSONDecodeError:
        return []

    return []


def _build_user_prompt(title: str, text_chunk: str) -> str:
    return (
        "Extract REAL user pain points from this Reddit content. "
        "Extract exactly ONE core pain point if the post has a single main problem. "
        "Return a second pain point ONLY if it is clearly distinct and equally strong. "
        "Do NOT break one problem into multiple variations. "
        "Do NOT generate generic or vague pain points. "
        "Return ONLY strict JSON with no extra text and no markdown.\n"
        "Expected JSON format:\n"
        "[\n"
        "  {\n"
        '    "pain_point": "...",\n'
        '    "headline": "...",\n'
        '    "severity": "low|medium|high",\n'
        '    "confidence": 0-1,\n'
        '    "willingness_to_pay": 0-1,\n'
        '    "emotional_intensity": 0-1\n'
        "  }\n"
        "]\n"
        "Return 1 item for most posts; max 2 items total.\n\n"
        f"title: {title.strip()[:300]}\n"
        f"chunk_text: {text_chunk.strip()[:2000]}\n"
    )


async def _analyze_chunk(
    client: httpx.AsyncClient,
    endpoint_url: str,
    model: str,
    headers: dict[str, str],
    title: str,
    text_chunk: str,
) -> dict[str, Any] | None:
    payload = {
        "model": model,
        "temperature": 0,
        "max_tokens": 400,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": _build_user_prompt(title=title, text_chunk=text_chunk)},
        ],
    }

    response = await client.post(endpoint_url, headers=headers, json=payload)
    response.raise_for_status()
    raw = _extract_message_content(response.json())
    items = _extract_json_payload(raw)
    if not items:
        return None

    return {"pain_points": items}


def _text_tokens(text: str) -> set[str]:
    words = re.findall(r"[a-z0-9]+", text.lower())
    return {word for word in words if word not in _STOPWORDS and len(word) > 2}


def _is_similar_pain_point(a: dict[str, Any], b: dict[str, Any]) -> bool:
    a_text = f"{a.get('pain_point', '')} {a.get('headline', '')}".strip().lower()
    b_text = f"{b.get('pain_point', '')} {b.get('headline', '')}".strip().lower()
    if not a_text or not b_text:
        return False
    if a_text == b_text:
        return True

    a_tokens = _text_tokens(a_text)
    b_tokens = _text_tokens(b_text)
    if not a_tokens or not b_tokens:
        return False

    overlap = len(a_tokens & b_tokens)
    union = len(a_tokens | b_tokens)
    jaccard = overlap / union if union else 0.0
    return jaccard >= 0.60


def _rank_key(item: dict[str, Any]) -> tuple[int, float, float]:
    return (
        _SEVERITY_RANK.get(_normalize_severity(item.get("severity")), 2),
        _to_unit_interval(item.get("willingness_to_pay"), default=0.0),
        _to_unit_interval(item.get("confidence"), default=0.0),
    )


def _normalize_candidate(item: dict[str, Any]) -> dict[str, Any] | None:
    pain_point = item.get("pain_point")
    headline = item.get("headline")
    if not isinstance(pain_point, str) or not pain_point.strip():
        return None
    if not isinstance(headline, str) or not headline.strip():
        return None

    return {
        "pain_point": pain_point.strip(),
        "headline": headline.strip(),
        "severity": _normalize_severity(item.get("severity")),
        "confidence": _to_unit_interval(item.get("confidence"), default=0.0),
        "willingness_to_pay": _to_unit_interval(item.get("willingness_to_pay"), default=0.0),
        "emotional_intensity": _to_unit_interval(item.get("emotional_intensity"), default=0.0),
    }


def _merge_chunk_candidates(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not candidates:
        return []

    normalized: list[dict[str, Any]] = []
    for item in candidates:
        normalized_item = _normalize_candidate(item)
        if normalized_item:
            normalized.append(normalized_item)

    if not normalized:
        return []

    # If LLM returned more than 2 items, keep only top-ranked candidates first.
    ranked = sorted(normalized, key=_rank_key, reverse=True)[:2]

    deduped: list[dict[str, Any]] = []
    for item in ranked:
        if any(_is_similar_pain_point(item, existing) for existing in deduped):
            continue
        deduped.append(item)

    if not deduped:
        return []

    if len(deduped) == 1:
        return deduped

    # Keep a second point only when it remains distinct and strong enough.
    first, second = deduped[0], deduped[1]
    first_strength = _rank_key(first)
    second_strength = _rank_key(second)
    if second_strength[0] < first_strength[0] and second_strength[2] < 0.65:
        return [first]

    return [first, second]


async def analyze_post(post: RedditPost) -> list[dict[str, Any]]:
    """Analyze one post and return up to two normalized pain point payloads."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error("OPENAI_API_KEY is not set; skipping post analysis")
        return []

    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    endpoint_url = _build_chat_completions_url(base_url)
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    title = (post.title or "").strip()
    body = (post.post_body or "").strip()
    if not title and not body:
        return []

    chunks = chunk_text(body, max_chars=2000) if body else []
    if not chunks:
        chunks = [title[:2000]] if title else []

    candidates: list[dict[str, Any]] = []
    async with httpx.AsyncClient(timeout=30.0) as client:
        for chunk in chunks:
            try:
                result = await async_retry(
                    lambda: asyncio.wait_for(
                        _analyze_chunk(
                            client=client,
                            endpoint_url=endpoint_url,
                            model=model,
                            headers=headers,
                            title=title,
                            text_chunk=chunk,
                        ),
                        timeout=35.0,
                    ),
                    retries=3,
                    backoff_base=0.5,
                    retry_exceptions=(httpx.HTTPError, asyncio.TimeoutError),
                )
            except Exception:
                logger.exception("Chunk analysis failed for reddit_id=%s", post.id)
                continue

            if isinstance(result, dict):
                items = result.get("pain_points")
                if isinstance(items, list):
                    candidates.extend([item for item in items if isinstance(item, dict)])

    merged = _merge_chunk_candidates(candidates)
    if not merged:
        return []

    output: list[dict[str, Any]] = []
    for item in merged:
        confidence = float(item["confidence"])
        willingness_to_pay = float(item["willingness_to_pay"])
        emotional_intensity = float(item["emotional_intensity"])
        severity = str(item["severity"])
        engagement_score = compute_engagement_score(
            upvotes=post.upvotes,
            num_comments=post.num_comments,
        )
        score = compute_final_score(
            severity=severity,
            emotional_intensity=emotional_intensity,
            willingness_to_pay=willingness_to_pay,
            confidence=confidence,
            engagement_score=engagement_score,
        )

        output.append(
            {
                "reddit_id": post.id,
                "pain_point": item["pain_point"],
                "pain_point_headline": item["headline"],
                "category": "general",
                "severity": severity,
                "emotional_intensity": emotional_intensity,
                "willingness_to_pay": willingness_to_pay,
                "confidence": confidence,
                "engagement_score": engagement_score,
                "score": score,
                "score_version": "v3",
                "score_reason": None,
            }
        )

    return output


async def extract_pain_points(posts: list[RedditPost]) -> list[dict[str, Any]]:
    """Compatibility helper: analyze posts one-by-one and return successful results."""
    extracted: list[dict[str, Any]] = []
    for post in posts:
        items = await analyze_post(post)
        extracted.extend(items)
    return extracted