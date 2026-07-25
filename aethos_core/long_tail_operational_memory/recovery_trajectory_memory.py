# SPDX-License-Identifier: Apache-2.0
"""Recovery trajectory memory — recovery evolution."""

from __future__ import annotations

from typing import Any

_TRAJECTORIES: list[str] = []


def record_recovery_trajectory(*, stage: str) -> dict[str, Any]:
    _TRAJECTORIES.append(stage)
    if len(_TRAJECTORIES) > 30:
        del _TRAJECTORIES[:-30]
    return {"trajectory_count": len(_TRAJECTORIES), "latest_stage": stage}
