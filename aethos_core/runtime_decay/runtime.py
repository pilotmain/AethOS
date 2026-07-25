# SPDX-License-Identifier: Apache-2.0
"""Runtime decay aggregate."""

from __future__ import annotations

from typing import Any

from aethos_core.runtime_decay.degradation_patterns import detect_degradation_patterns
from aethos_core.runtime_decay.dependency_decay import assess_dependency_decay
from aethos_core.runtime_decay.replay_erosion import assess_replay_erosion
from aethos_core.runtime_decay.restart_loop_decay import assess_restart_loop_decay
from aethos_core.runtime_decay.temporal_decay import assess_temporal_decay
from aethos_core.runtime_decay.topology_pressure import assess_topology_pressure


def assess_runtime_decay() -> dict[str, Any]:
    patterns = detect_degradation_patterns()
    restart = assess_restart_loop_decay()
    topology = assess_topology_pressure()
    replay = assess_replay_erosion()
    dependency = assess_dependency_decay()
    temporal = assess_temporal_decay()
    bounded = temporal.get("decay_bounded", True) and patterns.get("erosion_score", 1) < 0.5
    return {
        "ok": True,
        "degradation_patterns": patterns,
        "restart_loop_decay": restart,
        "topology_pressure": topology,
        "replay_erosion": replay,
        "dependency_decay": dependency,
        "temporal_decay": temporal,
        "decay_bounded": bounded,
        "summary": "Operational degradation gradual and bounded." if bounded else "Operational degradation patterns detected — monitoring active.",
    }
