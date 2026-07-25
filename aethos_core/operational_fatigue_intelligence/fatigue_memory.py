# SPDX-License-Identifier: Apache-2.0
"""Fatigue memory — fatigue trajectory history."""

from __future__ import annotations

from typing import Any

_FATIGUE_LOG: list[float] = []


def record_fatigue_memory(*, score: float = 0.33) -> dict[str, Any]:
    _FATIGUE_LOG.append(score)
    if len(_FATIGUE_LOG) > 50:
        del _FATIGUE_LOG[:-50]
    return {"fatigue_history_count": len(_FATIGUE_LOG), "latest_score": score}
