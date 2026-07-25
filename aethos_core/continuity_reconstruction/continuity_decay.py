# SPDX-License-Identifier: Apache-2.0
"""Continuity decay — operational thread aging and decay curves."""

from __future__ import annotations

from typing import Any

# Decay half-life in hours — threads lose relevance gradually, not abruptly.
_DEFAULT_HALF_LIFE_HOURS = 6.0
_STALE_THRESHOLD_HOURS = 24.0


def compute_continuity_decay(*, age_hours: float, half_life_hours: float = _DEFAULT_HALF_LIFE_HOURS) -> dict[str, Any]:
    """Exponential decay curve for thread relevance."""
    age = max(0.0, age_hours)
    decay_factor = 0.5 ** (age / max(half_life_hours, 0.1))
    stale = age >= _STALE_THRESHOLD_HOURS
    return {
        "age_hours": round(age, 2),
        "decay_factor": round(decay_factor, 3),
        "stale": stale,
        "relevance_weight": round(decay_factor if not stale else decay_factor * 0.5, 3),
        "summary": "Thread relevance fresh." if decay_factor >= 0.7 else "Thread relevance decaying." if not stale else "Thread relevance stale.",
    }


def apply_decay_to_confidence(*, base_confidence: float, age_hours: float) -> float:
    decay = compute_continuity_decay(age_hours=age_hours)
    return max(0.25, base_confidence * decay["relevance_weight"])
