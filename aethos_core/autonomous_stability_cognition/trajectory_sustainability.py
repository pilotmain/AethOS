# SPDX-License-Identifier: Apache-2.0
"""Trajectory sustainability — operational persistence."""

from __future__ import annotations

from typing import Any

from aethos_core.long_tail_operational_forecasting.operational_trajectory_projection import project_operational_trajectory


def assess_trajectory_sustainability() -> dict[str, Any]:
    trajectory = project_operational_trajectory()
    return {
        **trajectory,
        "trajectory_sustainable": trajectory.get("projection_stable", True),
        "summary": "Operational trajectory persistence within durable bounds.",
    }
