from __future__ import annotations

import json
import logging
import os
import asyncio
from typing import Any

import httpx
from dotenv import load_dotenv

from app.core.retry import async_retry
from app.schemas.reddit import RedditPost

logger = logging.getLogger(__name__)

load_dotenv()

SYSTEM_PROMPT = (
    "You are a startup analyst specializing in extracting actionable business pain points "
    "from user-generated content. Extract only real, explicit or strongly implied problems. "
    "Ignore generic opinions, hype, and fluff. Be concise. Do not hallucinate. "
    "Return ONLY a strict JSON list with items in this exact schema: "
    "{\"reddit_id\": string, \"pain_point\": string, \"category\": string, "
    "\"severity\": \"low\"|\"medium\"|\"high\"}."
)

async def extract_pain_points(posts: list[RedditPost]) -> list[dict]:
    """Extract structured business pain points from Reddit posts using an OpenAI-compatible API."""
    if not posts:
        return []

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error("OPENAI_API_KEY is not set; skipping pain-point extraction")
        return []

    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    endpoint_url = _build_chat_completions_url(base_url)

    extracted: list[dict] = []
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    logger.info("LLM endpoint configured as: %s", endpoint_url)

    async with httpx.AsyncClient(timeout=30.0) as client:
        for batch in _chunk_posts(posts, size=5):
            logger.info("Processing LLM batch of size %d", len(batch))
            try:
                batch_results = await async_retry(
                    lambda: asyncio.wait_for(
                        _extract_batch(
                            client=client,
                            endpoint_url=endpoint_url,
                            model=model,
                            headers=headers,
                            posts=batch,
                        ),
                        timeout=35.0,
                    ),
                    retries=3,
                    backoff_base=0.5,
                    retry_exceptions=(httpx.HTTPError, asyncio.TimeoutError),
                )
            except httpx.HTTPError:
                logger.exception("LLM request failed for batch; continuing with partial results")
                continue
            except asyncio.TimeoutError:
                logger.exception("LLM batch timed out after retries; continuing")
                continue
            except Exception:
                logger.exception("Unexpected LLM extraction error for batch; continuing")
                continue

            extracted.extend(batch_results)

    return extracted


def _chunk_posts(posts: list[RedditPost], size: int) -> list[list[RedditPost]]:
    return [posts[i : i + size] for i in range(0, len(posts), size)]


async def _extract_batch(
    client: httpx.AsyncClient,
    endpoint_url: str,
    model: str,
    headers: dict[str, str],
    posts: list[RedditPost],
) -> list[dict]:
    user_prompt = _build_user_prompt(posts)
    payload = {
        "model": model,
        "temperature": 0,
        "max_tokens": 1000,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    }

    response = await client.post(endpoint_url, headers=headers, json=payload)
    response.raise_for_status()

    data = response.json()
    raw_content = _extract_message_content(data)
    parsed = _safe_parse_json_list(raw_content)
    if not parsed:
        logger.warning("Skipping batch due to malformed or empty LLM JSON output")
        return []

    return _validate_items(parsed, allowed_ids={post.id for post in posts})


def _build_user_prompt(posts: list[RedditPost]) -> str:
    post_items = []
    for post in posts:
        post_items.append(
            {
                "reddit_id": post.id,
                "title": post.title[:300],
                "body": (post.selftext or "")[:1000],
            }
        )

    return (
        "Analyze the following Reddit posts and extract business pain points. "
        "Output ONLY a JSON list following the required schema.\n\n"
        f"POSTS:\n{json.dumps(post_items, ensure_ascii=True)}"
    )


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


def _safe_parse_json_list(raw: str) -> list[dict[str, Any]]:
    if not raw:
        return []

    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.startswith("json"):
            cleaned = cleaned[4:].strip()

    for candidate in (cleaned, _extract_array_slice(cleaned)):
        if not candidate:
            continue
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, list):
            return [item for item in parsed if isinstance(item, dict)]
        if isinstance(parsed, dict):
            for key in ("pain_points", "items", "results", "data"):
                value = parsed.get(key)
                if isinstance(value, list):
                    return [item for item in value if isinstance(item, dict)]

    return []


def _extract_array_slice(text: str) -> str:
    start = text.find("[")
    end = text.rfind("]")
    if start == -1 or end == -1 or end <= start:
        return ""
    return text[start : end + 1]


def _build_chat_completions_url(base_url: str) -> str:
    normalized = (base_url or "").strip().rstrip("/")
    if not normalized:
        normalized = "https://api.openai.com/v1"
    return f"{normalized}/chat/completions"


def _validate_items(items: list[dict[str, Any]], allowed_ids: set[str]) -> list[dict]:
    valid: list[dict] = []
    seen_ids: set[str] = set()

    for item in items:
        reddit_id = item.get("reddit_id")
        pain_point = item.get("pain_point")
        category = item.get("category")
        severity = item.get("severity")

        if not isinstance(reddit_id, str) or reddit_id not in allowed_ids:
            continue
        if reddit_id in seen_ids:
            continue
        if not isinstance(pain_point, str) or not pain_point.strip():
            continue
        if not isinstance(category, str) or not category.strip():
            continue
        if not isinstance(severity, str):
            continue

        normalized_severity = severity.strip().lower()
        if normalized_severity not in {"low", "medium", "high"}:
            continue

        valid.append(
            {
                "reddit_id": reddit_id,
                "pain_point": pain_point.strip(),
                "category": category.strip(),
                "severity": normalized_severity,
            }
        )
        seen_ids.add(reddit_id)

    return valid
