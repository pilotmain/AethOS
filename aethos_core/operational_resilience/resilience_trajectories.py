# SPDX-License-Identifier: Apache-2.0
"""Resilience trajectories — long-tail stability evolution."""

from __future__ import annotations

from typing import Any

from aethos_core.operational_resilience_cognition.resilience_trajectories import track_resilience_trajectories


def track_operational_resilience_trajectories(*, current_score: float = 0.88) -> dict[str, Any]:
    trajectories = track_resilience_trajectories(current_score=current_score)
    return {
        **trajectories,
        "summary": "Long-tail stability evolution remains positive across sustained windows.",
    }
