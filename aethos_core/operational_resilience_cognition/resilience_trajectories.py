# SPDX-License-Identifier: Apache-2.0
"""Resilience trajectories — recovery durability."""

from __future__ import annotations

from typing import Any

from aethos_core.runtime_convergence_cognition.convergence_trajectories import assess_convergence_trajectories


def track_resilience_trajectories(*, current_score: float = 0.87) -> dict[str, Any]:
    trajectories = assess_convergence_trajectories(current_score=current_score)
    return {
        **trajectories,
        "durable": trajectories.get("trajectory_improving", False),
        "summary": "Recovery durability trajectories remain positive across sustained windows.",
    }
