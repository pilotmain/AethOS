# SPDX-License-Identifier: Apache-2.0
"""Confidence history — reliability trend evolution."""

from __future__ import annotations

from typing import Any

_CONFIDENCE_HISTORY: list[dict[str, Any]] = []


def record_confidence_snapshot(*, score: float, phase: str) -> None:
    _CONFIDENCE_HISTORY.append({"score": score, "phase": phase})
    if len(_CONFIDENCE_HISTORY) > 100:
        del _CONFIDENCE_HISTORY[:-100]


def confidence_history_state() -> dict[str, Any]:
    scores = [e["score"] for e in _CONFIDENCE_HISTORY if "score" in e]
    trend = "stable"
    if len(scores) >= 2:
        trend = "improving" if scores[-1] >= scores[-2] else "declining"
    return {
        "entries": list(_CONFIDENCE_HISTORY[-15:]),
        "count": len(_CONFIDENCE_HISTORY),
        "trend": trend,
        "summary": f"Confidence trend: {trend}.",
    }
