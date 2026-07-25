# SPDX-License-Identifier: Apache-2.0
"""Continuity memory — historical recovery behavior."""

from __future__ import annotations

from typing import Any

_HISTORY: list[dict[str, Any]] = []


def record_continuity_memory(*, stable: bool) -> dict[str, Any]:
    entry = {"stable": stable}
    _HISTORY.append(entry)
    if len(_HISTORY) > 50:
        del _HISTORY[:-50]
    return {"history_count": len(_HISTORY), "latest": entry}
