# SPDX-License-Identifier: Apache-2.0
"""Deduplication — overlap cleanup."""

from __future__ import annotations

from typing import Any


def dedupe_recommendations(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for item in items:
        key = (item.get("name") or "").strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out
