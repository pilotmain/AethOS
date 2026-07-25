# SPDX-License-Identifier: Apache-2.0
"""Operational pattern memory — long-tail operational intuition."""

from __future__ import annotations

from typing import Any

_PATTERNS: list[str] = []


def remember_operational_pattern(*, pattern: str) -> dict[str, Any]:
    _PATTERNS.append(pattern)
    if len(_PATTERNS) > 30:
        del _PATTERNS[:-30]
    return {"pattern_count": len(_PATTERNS), "latest": pattern}
