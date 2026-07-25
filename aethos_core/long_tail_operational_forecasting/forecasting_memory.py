# SPDX-License-Identifier: Apache-2.0
"""Forecasting memory — long-tail operational history."""

from __future__ import annotations

from typing import Any

_HISTORY: list[dict[str, Any]] = []


def record_forecasting_memory(*, survivable: bool) -> dict[str, Any]:
    entry = {"survivable": survivable}
    _HISTORY.append(entry)
    if len(_HISTORY) > 50:
        del _HISTORY[:-50]
    return {"forecast_history_count": len(_HISTORY), "latest": entry}
