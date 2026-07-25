# SPDX-License-Identifier: Apache-2.0
"""Sustained resilience memory — long-tail resilience history."""

from __future__ import annotations

from typing import Any

_HISTORY: list[dict[str, Any]] = []


def record_sustained_resilience(*, resilient: bool) -> dict[str, Any]:
    entry = {"resilient": resilient}
    _HISTORY.append(entry)
    if len(_HISTORY) > 50:
        del _HISTORY[:-50]
    return {"history_count": len(_HISTORY), "latest": entry}
