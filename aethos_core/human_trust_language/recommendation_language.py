# SPDX-License-Identifier: Apache-2.0
"""Recommendation language — recommendation elegance."""

from __future__ import annotations

from typing import Any


def format_recommendation_line(item: dict[str, Any]) -> str:
    name = item.get("name", "Recommendation")
    location = item.get("location") or ""
    explanation = item.get("explanation") or item.get("description", "")
    loc = f" — {location}" if location else ""
    return f"**{name}**{loc}\n{explanation}"
