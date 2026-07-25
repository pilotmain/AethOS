# SPDX-License-Identifier: Apache-2.0
"""Instability prediction — early degradation indicators."""

from __future__ import annotations

from typing import Any


def predict_instability(*, drift: dict[str, Any]) -> dict[str, Any]:
    entropy = drift.get("entropy", {}).get("entropy_score", 0)
    degradation = drift.get("degradation", {}).get("degradation_detected", False)
    risk = min(1.0, entropy + (0.2 if degradation else 0))
    return {
        "instability_risk": round(risk, 2),
        "early_indicators": degradation or entropy >= 0.2,
        "summary": "Early instability indicators detected." if risk >= 0.3 else "No early instability indicators.",
    }
