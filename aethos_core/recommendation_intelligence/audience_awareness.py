# SPDX-License-Identifier: Apache-2.0
"""Audience awareness — age/family targeting."""

from __future__ import annotations

from typing import Any


def apply_audience_context(items: list[dict[str, Any]], *, audience: str) -> list[dict[str, Any]]:
    if audience != "family":
        return items
    family_kw = ("playground", "kids", "children", "family", "toddler", "shaded")
    scored: list[dict[str, Any]] = []
    for item in items:
        text = f"{item.get('name', '')} {item.get('description', '')}".lower()
        boost = 0.15 if any(k in text for k in family_kw) else 0.0
        item = dict(item)
        item["score"] = float(item.get("score") or 0) + boost
        scored.append(item)
    return scored
