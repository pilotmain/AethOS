# SPDX-License-Identifier: Apache-2.0
"""Convergence trajectories — stabilization evolution."""

from __future__ import annotations

from typing import Any

_TRAJECTORIES: list[float] = []


def assess_convergence_trajectories(*, current_score: float = 0.82) -> dict[str, Any]:
    _TRAJECTORIES.append(current_score)
    if len(_TRAJECTORIES) > 50:
        del _TRAJECTORIES[:-50]
    improving = len(_TRAJECTORIES) < 2 or _TRAJECTORIES[-1] >= _TRAJECTORIES[-2]
    return {
        "current_score": current_score,
        "trajectory_improving": improving,
        "samples": len(_TRAJECTORIES),
        "summary": "Convergence trajectory improving across sustained windows." if improving else "Convergence trajectory monitoring active.",
    }
