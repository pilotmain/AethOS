# SPDX-License-Identifier: Apache-2.0
"""Resilience decay — resilience weakening."""

from __future__ import annotations

from typing import Any

from aethos_core.operational_resilience_cognition.degradation_resilience import assess_degradation_resilience


def assess_resilience_decay(*, hours: float = 9.0) -> dict[str, Any]:
    decay = assess_degradation_resilience(hours=hours)
    return {
        **decay,
        "weakening": not decay.get("erosion_resistant", True),
        "summary": "Resilience weakening within bounded limits." if decay.get("erosion_resistant") else "Resilience decay emerging.",
    }
