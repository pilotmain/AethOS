# SPDX-License-Identifier: Apache-2.0
"""Stabilization exhaustion — prolonged stabilization pressure."""

from __future__ import annotations

from typing import Any

from aethos_core.operational_fatigue_intelligence.stabilization_fatigue import assess_stabilization_fatigue


def assess_stabilization_exhaustion() -> dict[str, Any]:
    fatigue = assess_stabilization_fatigue()
    return {
        **fatigue,
        "exhaustion_emerging": fatigue.get("fatigued", False),
        "summary": (
            "Operational recovery continues to remain resilient across sustained runtime verification windows, "
            "though prolonged operational endurance pressure continues to be monitored for emerging resilience exhaustion trajectories."
        ),
    }
