from __future__ import annotations

from typing import List


def chunk_text(text: str, max_chars: int = 2000) -> List[str]:
    """Split text into chunks up to max_chars, preferring paragraph boundaries."""
    if max_chars <= 0:
        return []

    normalized = (text or "").strip()
    if not normalized:
        return []
    if len(normalized) <= max_chars:
        return [normalized]

    paragraphs = [part.strip() for part in normalized.split("\n\n") if part and part.strip()]
    chunks: list[str] = []
    current = ""

    for paragraph in paragraphs:
        if len(paragraph) > max_chars:
            if current:
                chunks.append(current)
                current = ""
            chunks.extend(_hard_split(paragraph, max_chars))
            continue

        if not current:
            current = paragraph
            continue

        candidate = f"{current}\n\n{paragraph}"
        if len(candidate) <= max_chars:
            current = candidate
        else:
            chunks.append(current)
            current = paragraph

    if current:
        chunks.append(current)

    return [chunk for chunk in chunks if chunk]


def _hard_split(text: str, max_chars: int) -> list[str]:
    pieces: list[str] = []
    start = 0
    while start < len(text):
        pieces.append(text[start : start + max_chars])
        start += max_chars
    return pieces