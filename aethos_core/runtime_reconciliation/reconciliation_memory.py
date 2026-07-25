# SPDX-License-Identifier: Apache-2.0
"""Reconciliation memory — reconciliation history."""

from __future__ import annotations

from typing import Any

_HISTORY: list[dict[str, Any]] = []


def record_reconciliation(*, surface: str, aligned: bool) -> dict[str, Any]:
    entry = {"surface": surface, "aligned": aligned}
    _HISTORY.append(entry)
    if len(_HISTORY) > 100:
        del _HISTORY[:-100]
    return {"history_count": len(_HISTORY), "latest": entry}
