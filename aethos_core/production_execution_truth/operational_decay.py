# SPDX-License-Identifier: Apache-2.0
"""Operational decay — confidence degradation over time."""

from __future__ import annotations

from typing import Any

_DECAY_SAMPLES: list[float] = []


def assess_operational_decay(*, base_confidence: float = 0.82, hours_elapsed: float = 0.0) -> dict[str, Any]:
    decay_rate = 0.02 * max(0.0, hours_elapsed)
    current = max(0.35, base_confidence - decay_rate)
    bounded = current >= 0.65
    _DECAY_SAMPLES.append(current)
    if len(_DECAY_SAMPLES) > 100:
        del _DECAY_SAMPLES[:-100]
    return {
        "base_confidence": base_confidence,
        "current_confidence": round(current, 2),
        "decay_bounded": bounded,
        "hours_elapsed": hours_elapsed,
        "summary": "Operational decay bounded within acceptable confidence thresholds."
        if bounded
        else "Operational decay detected — extended verification recommended.",
    }
