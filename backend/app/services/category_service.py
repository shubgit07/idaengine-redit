from __future__ import annotations

import re
from typing import Final

_ALLOWED_CATEGORIES: Final[set[str]] = {
    "acquisition",
    "activation",
    "retention",
    "pricing",
    "support",
    "operations",
    "product",
    "technical",
    "compliance",
    "marketplace",
    "finance",
    "general",
}

_KEYWORD_RULES: Final[list[tuple[str, tuple[str, ...]]]] = [
    (
        "acquisition",
        (
            "customer acquisition",
            "lead generation",
            "ads",
            "advertising",
            "seo",
            "traffic",
            "marketing",
            "cold email",
            "conversion",
            "funnel",
        ),
    ),
    (
        "activation",
        (
            "onboarding",
            "activation",
            "signup",
            "sign up",
            "first-time user",
            "time to value",
            "trial",
        ),
    ),
    (
        "retention",
        (
            "churn",
            "retention",
            "renewal",
            "stickiness",
            "engagement drop",
            "cancellation",
            "inactive users",
        ),
    ),
    (
        "pricing",
        (
            "pricing",
            "price",
            "charge",
            "subscription",
            "plan",
            "billing",
            "too expensive",
            "willing to pay",
        ),
    ),
    (
        "support",
        (
            "support",
            "customer service",
            "ticket",
            "response time",
            "refund",
            "complaint",
        ),
    ),
    (
        "operations",
        (
            "process",
            "workflow",
            "ops",
            "manual",
            "automation",
            "hiring",
            "team",
            "logistics",
            "fulfillment",
            "inventory",
        ),
    ),
    (
        "product",
        (
            "feature",
            "product",
            "ux",
            "ui",
            "roadmap",
            "bug",
            "missing",
            "integration",
        ),
    ),
    (
        "technical",
        (
            "api",
            "database",
            "latency",
            "performance",
            "outage",
            "error",
            "crash",
            "infrastructure",
            "security",
        ),
    ),
    (
        "compliance",
        (
            "gdpr",
            "compliance",
            "legal",
            "tax",
            "privacy",
            "regulation",
            "license",
        ),
    ),
    (
        "marketplace",
        (
            "supply",
            "demand",
            "marketplace",
            "liquidity",
            "buyer",
            "seller",
            "two-sided",
        ),
    ),
    (
        "finance",
        (
            "cashflow",
            "cash flow",
            "runway",
            "fundraising",
            "profit",
            "margin",
            "burn",
            "revenue",
            "cost",
        ),
    ),
]


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower())


def normalize_category(
    raw_category: str | None,
    *,
    pain_point: str = "",
    headline: str = "",
    context_text: str = "",
) -> str:
    if isinstance(raw_category, str) and raw_category.strip():
        candidate = _normalize_text(raw_category)
        # Keep explicit categories, but re-infer for legacy/default "general" rows.
        if candidate in _ALLOWED_CATEGORIES and candidate != "general":
            return candidate

    inferred = infer_category(f"{headline} {pain_point} {context_text}")
    if inferred != "general":
        return inferred

    return "general"


def infer_category(text: str) -> str:
    normalized = _normalize_text(text)
    if not normalized:
        return "general"

    for category, keywords in _KEYWORD_RULES:
        if any(keyword in normalized for keyword in keywords):
            return category

    return "general"
