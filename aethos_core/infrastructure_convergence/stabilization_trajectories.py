# SPDX-License-Identifier: Apache-2.0
"""Stabilization trajectories — runtime evolution."""

from __future__ import annotations

from typing import Any

from aethos_core.runtime_convergence_cognition.convergence_trajectories import assess_convergence_trajectories


def track_stabilization_trajectories(*, current_score: float = 0.84) -> dict[str, Any]:
    return assess_convergence_trajectories(current_score=current_score)
