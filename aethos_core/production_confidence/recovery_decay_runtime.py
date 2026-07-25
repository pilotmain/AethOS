# SPDX-License-Identifier: Apache-2.0
"""Recovery decay runtime — confidence erosion."""

from __future__ import annotations

from typing import Any


def assess_recovery_decay(*, predictive: dict[str, Any]) -> dict[str, Any]:
    decay = predictive.get("confidence_forecast", {}).get("projected_decay_24h", 0)
    erosion = decay >= 0.25
    return {
        "recovery_decay": round(decay, 2),
        "erosion_active": erosion,
        "summary": "Confidence erosion within bounds." if not erosion else "Recovery confidence erosion detected.",
    }
