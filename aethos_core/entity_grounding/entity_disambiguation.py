# SPDX-License-Identifier: Apache-2.0
"""Entity grounding — disambiguate AethOS platform from unrelated entities."""

from __future__ import annotations

import re
from typing import Any

_PLATFORM_MARKERS = (
    "operational intelligence platform",
    "mission control",
    "infrastructure orchestration",
    "telegram operational runtime",
    "provider operational grounding",
)

_UNRELATED_MARKERS = (
    "bicycle",
    "bike",
    "cycling",
    "sportswear",
    "retail brand",
)


def ground_entity_query(*, query: str, session_id: str = "default") -> dict[str, Any]:
    """Anchor research/operational queries to the user's AethOS platform when ambiguous."""
    lower = (query or "").lower()
    mentions_aethos = bool(re.search(r"\baethos\b", lower, re.I))
    if not mentions_aethos:
        return {"grounded": False, "entity": None, "query": query}

    unrelated_hit = any(m in lower for m in _UNRELATED_MARKERS)
    platform_context = (
        "AethOS refers to the user's operational intelligence platform — "
        "infrastructure orchestration, Mission Control, provider grounding, and Telegram operational runtime. "
        "NOT bicycles, sportswear, or unrelated commercial products."
    )

    grounded_query = query
    if unrelated_hit or "competitor" in lower or "market" in lower or "gtm" in lower:
        grounded_query = f"{query}\n\nEntity anchor: {platform_context}"

    return {
        "grounded": True,
        "entity": "aethos_platform",
        "platform_context": platform_context,
        "query": query,
        "grounded_query": grounded_query,
        "disambiguation_required": unrelated_hit or "market" in lower,
        "summary": "Entity grounded to AethOS operational intelligence platform.",
    }
