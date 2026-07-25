# SPDX-License-Identifier: Apache-2.0
"""Runtime endurance — operational persistence."""

from __future__ import annotations

from typing import Any

from aethos_core.operational_fatigue_cognition.operational_exhaustion import assess_operational_exhaustion


def assess_runtime_endurance() -> dict[str, Any]:
    endurance = assess_operational_exhaustion()
    return {
        **endurance,
        "enduring": not endurance.get("accelerating", False),
        "summary": "Operational persistence within durable bounds.",
    }
