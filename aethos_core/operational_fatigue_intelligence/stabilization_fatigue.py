# SPDX-License-Identifier: Apache-2.0
"""Stabilization fatigue — prolonged stabilization pressure."""

from __future__ import annotations

from typing import Any

from aethos_core.long_tail_stability.recovery_fragility import detect_recovery_fragility


def assess_stabilization_fatigue() -> dict[str, Any]:
    fragility = detect_recovery_fragility()
    fatigued = fragility.get("fragile", False)
    return {
        **fragility,
        "fatigued": fatigued,
        "summary": (
            "Operational recovery remains resilient across sustained verification windows, "
            "though prolonged runtime stabilization pressure continues to be monitored for emerging fatigue trajectories."
        ),
    }
