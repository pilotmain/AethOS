# SPDX-License-Identifier: Apache-2.0
"""Instability trajectories — degradation evolution."""

from __future__ import annotations

from typing import Any

from aethos_core.operational_resilience.resilience_trajectories import track_operational_resilience_trajectories


def track_instability_trajectories(*, current_score: float = 0.85) -> dict[str, Any]:
    trajectories = track_operational_resilience_trajectories(current_score=current_score)
    return {
        **trajectories,
        "summary": "Degradation evolution trajectories within acceptable bounds.",
    }
