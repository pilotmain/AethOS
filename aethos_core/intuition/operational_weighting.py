# SPDX-License-Identifier: Apache-2.0
"""Operational weighting — urgency vs noise."""

from __future__ import annotations

from typing import Any


def weight_operational_signals(
    *,
    items: list[dict[str, Any]] | None = None,
    focus_topics: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Rank items by operational relevance vs noise."""
    focus = " ".join(focus_topics or []).lower()
    weighted: list[dict[str, Any]] = []
    for item in items or []:
        title = str(item.get("title") or item.get("summary") or item.get("text") or "")
        tl = title.lower()
        score = float(item.get("priority_score") or item.get("score") or 0.5)
        if any(k in tl for k in ("outage", "production", "critical", "verification_failed")):
            score += 0.35
        if focus and any(k in tl for k in focus.split() if len(k) > 3):
            score += 0.2
        if any(k in tl for k in ("dependency modernization", "low priority", "informational")):
            score -= 0.25
        weighted.append({**item, "operational_weight": round(min(1.0, max(0.0, score)), 2)})
    return sorted(weighted, key=lambda x: x.get("operational_weight", 0), reverse=True)
