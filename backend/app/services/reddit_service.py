from __future__ import annotations

import asyncio
import logging
import random
from typing import Any
import xml.etree.ElementTree as ET

import httpx
from pydantic import ValidationError

from app.schemas.reddit import RedditPost

logger = logging.getLogger(__name__)


class RedditServiceError(Exception):
    """Raised when RedditService fails to fetch or parse data from Reddit."""


class RedditService:
    BASE_URL = "https://www.reddit.com"
    DEFAULT_HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.google.com/",
    }
    ALLOWED_TIME_FILTERS = {"day", "week", "month", "year", "all"}

    def __init__(
        self,
        client: httpx.AsyncClient | None = None,
        timeout: float = 10.0,
        max_retries: int = 3,
        backoff_base: float = 0.5,
    ) -> None:
        self._owns_client = client is None
        self._client = client or httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers=self.DEFAULT_HEADERS,
            timeout=httpx.Timeout(timeout, connect=5.0),
            follow_redirects=True,
            http2=True,
        )
        self._max_retries = max_retries
        self._backoff_base = backoff_base

    async def fetch_top_posts_for_subreddits(
        self,
        subreddits: list[str],
        limit: int = 10,
        time_filter: str = "day",
        min_delay_seconds: float = 20.0,
        max_delay_seconds: float = 30.0,
    ) -> list[RedditPost]:
        if min_delay_seconds < 0 or max_delay_seconds < 0:
            raise ValueError("delay values must be non-negative")
        if min_delay_seconds > max_delay_seconds:
            raise ValueError("min_delay_seconds must be <= max_delay_seconds")

        combined: list[RedditPost] = []

        # Intentionally sequential to avoid bursty traffic patterns.
        for index, subreddit in enumerate(subreddits):
            if index > 0:
                delay = random.uniform(min_delay_seconds, max_delay_seconds)
                logger.info(
                    "Polite delay before next subreddit request: %.2fs",
                    delay,
                )
                await asyncio.sleep(delay)

            posts = await self.fetch_top_posts(
                subreddit=subreddit,
                limit=limit,
                time_filter=time_filter,
            )
            combined.extend(posts)

        return combined

    async def close(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def __aenter__(self) -> "RedditService":
        return self

    async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        await self.close()

    async def fetch_top_posts(
        self,
        subreddit: str,
        limit: int = 10,
        time_filter: str = "day",
    ) -> list[RedditPost]:
        if not subreddit or not subreddit.strip():
            raise ValueError("subreddit must be a non-empty string")
        if limit <= 0:
            raise ValueError("limit must be greater than 0")
        if time_filter not in self.ALLOWED_TIME_FILTERS:
            raise ValueError(
                f"time_filter must be one of: {', '.join(sorted(self.ALLOWED_TIME_FILTERS))}"
            )

        subreddit_name = subreddit.strip().lstrip("r/").strip("/")
        json_endpoint = f"/r/{subreddit_name}/top.json"
        rss_endpoint = f"/r/{subreddit_name}/top.rss"
        params = {"limit": limit, "t": time_filter}

        logger.info("Fetching top posts from subreddit '%s'", subreddit_name)

        response = await self._request_with_retries(
            endpoint=json_endpoint,
            params=params,
            subreddit_name=subreddit_name,
        )

        if response.status_code == 403:
            logger.warning(
                "Received 403 for JSON endpoint /r/%s. Falling back to RSS endpoint.",
                subreddit_name,
            )
            rss_response = await self._request_with_retries(
                endpoint=rss_endpoint,
                params=params,
                subreddit_name=subreddit_name,
            )
            if rss_response.status_code != 200:
                raise RedditServiceError(
                    f"Reddit RSS fallback returned status {rss_response.status_code} for /r/{subreddit_name}"
                )
            logger.info("Fetch source for subreddit '%s': rss_fallback", subreddit_name)
            return _parse_reddit_rss_posts(rss_response.text, subreddit_name=subreddit_name, limit=limit)

        if response is None:
            raise RedditServiceError(f"No response received for /r/{subreddit_name}")

        if response.status_code != 200:
            raise RedditServiceError(
                f"Reddit returned status {response.status_code} for /r/{subreddit_name}"
            )

        logger.info("Fetch source for subreddit '%s': json", subreddit_name)

        try:
            payload = response.json()
        except Exception as exc:
            raise RedditServiceError("Invalid JSON response from Reddit") from exc

        children = payload.get("data", {}).get("children", [])
        if not children:
            logger.info("No posts found for subreddit '%s'", subreddit_name)
            return []

        posts: list[RedditPost] = []
        for item in children:
            data = item.get("data", {})
            try:
                posts.append(
                    RedditPost(
                        id=data["id"],
                        title=data["title"],
                        selftext=data.get("selftext", ""),
                        author=data.get("author", ""),
                        score=data.get("score", 0),
                        num_comments=data.get("num_comments", 0),
                        created_utc=data.get("created_utc", 0.0),
                        url=data.get("url", ""),
                    )
                )
            except (KeyError, ValidationError, TypeError, ValueError) as exc:
                logger.warning("Skipping invalid Reddit post in subreddit '%s': %s", subreddit_name, exc)
                continue

        logger.info(
            "Fetched %d valid posts from subreddit '%s'",
            len(posts),
            subreddit_name,
        )
        return posts

    async def _request_with_retries(
        self,
        endpoint: str,
        params: dict[str, Any],
        subreddit_name: str,
    ) -> httpx.Response:
        response: httpx.Response | None = None

        for attempt in range(1, self._max_retries + 1):
            try:
                response = await asyncio.wait_for(
                    self._client.get(endpoint, params=params),
                    timeout=15,
                )
            except (httpx.RequestError, asyncio.TimeoutError) as exc:
                if attempt >= self._max_retries:
                    raise RedditServiceError(
                        f"Network error fetching {endpoint} for /r/{subreddit_name} after {self._max_retries} attempts"
                    ) from exc

                sleep_time = self._backoff_base * (2 ** (attempt - 1))
                logger.warning(
                    "Request attempt %d/%d failed for %s: %s. Retrying in %.2fs",
                    attempt,
                    self._max_retries,
                    endpoint,
                    exc,
                    sleep_time,
                )
                await asyncio.sleep(sleep_time)
                continue

            if response.status_code == 429:
                retry_after = _parse_retry_after_seconds(response)
                logger.warning(
                    "Rate limited by Reddit on %s for subreddit '%s'. Waiting %.2fs before retry (%d/%d)",
                    endpoint,
                    subreddit_name,
                    retry_after,
                    attempt,
                    self._max_retries,
                )
                if attempt >= self._max_retries:
                    raise RedditServiceError(
                        f"Rate limited by Reddit on {endpoint} for /r/{subreddit_name} after {self._max_retries} attempts"
                    )

                await asyncio.sleep(retry_after)
                continue

            return response

        if response is None:
            raise RedditServiceError(f"No response received for endpoint {endpoint}")
        return response


def _parse_retry_after_seconds(response: httpx.Response, fallback: float = 10.0) -> float:
    value = response.headers.get("Retry-After", "").strip()
    if not value:
        return fallback

    try:
        parsed = float(value)
    except ValueError:
        return fallback

    if parsed < 0:
        return fallback
    return parsed


def _parse_reddit_rss_posts(text: str, subreddit_name: str, limit: int) -> list[RedditPost]:
    try:
        root = ET.fromstring(text)
    except ET.ParseError as exc:
        raise RedditServiceError(f"Invalid RSS response from Reddit for /r/{subreddit_name}") from exc

    namespace = {"atom": "http://www.w3.org/2005/Atom"}
    entries = root.findall("atom:entry", namespace)

    posts: list[RedditPost] = []
    for entry in entries[:limit]:
        reddit_id = _extract_reddit_id_from_rss_entry(entry, namespace)
        title = (entry.findtext("atom:title", default="", namespaces=namespace) or "").strip()
        author = (
            entry.findtext("atom:author/atom:name", default="", namespaces=namespace) or ""
        ).strip()
        link = _extract_link_from_rss_entry(entry, namespace)
        updated_raw = entry.findtext("atom:updated", default="", namespaces=namespace)

        if not reddit_id or not title or not link:
            continue

        posts.append(
            RedditPost(
                id=reddit_id,
                title=title,
                selftext="",
                author=author,
                score=0,
                num_comments=0,
                created_utc=_iso8601_to_epoch(updated_raw),
                url=link,
            )
        )

    logger.info(
        "Fetched %d valid posts from subreddit '%s' via RSS fallback",
        len(posts),
        subreddit_name,
    )
    return posts


def _extract_reddit_id_from_rss_entry(entry: ET.Element, namespace: dict[str, str]) -> str:
    identifier = (entry.findtext("atom:id", default="", namespaces=namespace) or "").strip()
    if "/comments/" not in identifier:
        return ""

    parts = [part for part in identifier.split("/") if part]
    try:
        comments_index = parts.index("comments")
    except ValueError:
        return ""

    if comments_index + 1 >= len(parts):
        return ""
    return parts[comments_index + 1]


def _extract_link_from_rss_entry(entry: ET.Element, namespace: dict[str, str]) -> str:
    link = entry.find("atom:link", namespace)
    if link is None:
        return ""
    return (link.attrib.get("href", "") or "").strip()


def _iso8601_to_epoch(value: str) -> float:
    if not value:
        return 0.0

    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"

    try:
        from datetime import datetime

        return datetime.fromisoformat(normalized).timestamp()
    except ValueError:
        return 0.0
