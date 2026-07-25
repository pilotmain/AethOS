# SPDX-License-Identifier: Apache-2.0
"""Long-tail operational decay aggregate."""

from __future__ import annotations

from typing import Any

from aethos_core.long_tail_operational_decay.degradation_trajectory import assess_degradation_trajectory
from aethos_core.long_tail_operational_decay.dependency_decay_tracking import track_dependency_decay
from aethos_core.long_tail_operational_decay.replay_decay_tracking import track_replay_decay
from aethos_core.long_tail_operational_decay.stabilization_regression import assess_stabilization_regression
from aethos_core.long_tail_operational_decay.temporal_operational_decay import assess_temporal_operational_decay
from aethos_core.long_tail_operational_decay.topology_erosion import assess_topology_erosion


def assess_long_tail_operational_decay() -> dict[str, Any]:
    trajectory = assess_degradation_trajectory()
    replay = track_replay_decay()
    dependency = track_dependency_decay()
    topology = assess_topology_erosion()
    temporal = assess_temporal_operational_decay()
    regression = assess_stabilization_regression(stable=True)
    bounded = temporal.get("decay_bounded", True) and not regression.get("regression_detected")
    return {
        "ok": True,
        "degradation_trajectory": trajectory,
        "replay_decay": replay,
        "dependency_decay": dependency,
        "topology_erosion": topology,
        "temporal_decay": temporal,
        "stabilization_regression": regression,
        "decay_bounded": bounded,
        "summary": "Long-tail operational decay bounded — progressive degradation within acceptable limits."
        if bounded
        else "Long-tail operational decay detected — convergence monitoring active.",
    }
