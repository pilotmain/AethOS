# SPDX-License-Identifier: Apache-2.0
"""Temporal confidence — confidence persistence over time."""

from __future__ import annotations

from typing import Any


def assess_temporal_confidence(*, verification: dict[str, Any], history: dict[str, Any]) -> dict[str, Any]:
    sustained = verification.get("sustained", False)
    trend = history.get("confidence", {}).get("trend") or "stable"
    score = 0.85 if sustained and trend != "declining" else 0.65 if sustained else 0.45
    return {
        "temporal_confidence": round(score, 2),
        "persists": score >= 0.7,
        "summary": "Confidence persists over extended verification." if score >= 0.7 else "Temporal confidence requires longer observation.",
    }
