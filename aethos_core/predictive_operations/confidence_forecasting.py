# SPDX-License-Identifier: Apache-2.0
"""Confidence forecasting — future confidence decay."""

from __future__ import annotations

from typing import Any


def forecast_confidence_decay(*, verification: dict[str, Any], drift: dict[str, Any]) -> dict[str, Any]:
    current_decay = verification.get("decay", {}).get("verification_decay", 0)
    entropy = drift.get("entropy", {}).get("entropy_score", 0)
    projected = min(0.5, current_decay + entropy * 0.15)
    return {
        "projected_decay_24h": round(projected, 2),
        "confidence_persists": projected < 0.2,
        "summary": "Future confidence decay within bounds." if projected < 0.2 else "Projected confidence decay requires monitoring.",
    }
