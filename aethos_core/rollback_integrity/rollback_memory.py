# SPDX-License-Identifier: Apache-2.0
"""Rollback memory — rollback outcome history."""

from __future__ import annotations

from typing import Any

_HISTORY: list[dict[str, Any]] = []


def record_rollback_outcome(*, provider: str, verified: bool) -> dict[str, Any]:
    entry = {"provider": provider, "verified": verified}
    _HISTORY.append(entry)
    if len(_HISTORY) > 50:
        del _HISTORY[:-50]
    return {"history_count": len(_HISTORY), "latest": entry}
