# SPDX-License-Identifier: Apache-2.0
"""Operational truth decay — confidence degradation."""

from __future__ import annotations

from typing import Any


def assess_infrastructure_decay(*, base_confidence: float = 0.8) -> dict[str, Any]:
    hours_elapsed = 1.5
    decay_rate = 0.02 * max(0.0, hours_elapsed)
    current = max(0.35, base_confidence - decay_rate)
    bounded = current >= 0.65
    return {
        "base_confidence": base_confidence,
        "current_confidence": round(current, 2),
        "decay_bounded": bounded,
        "hours_elapsed": hours_elapsed,
        "summary": "Operational decay bounded within acceptable confidence thresholds."
        if bounded
        else "Operational decay detected — extended verification recommended.",
    }
