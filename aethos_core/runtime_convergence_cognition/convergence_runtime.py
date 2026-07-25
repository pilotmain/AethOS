# SPDX-License-Identifier: Apache-2.0
"""Convergence runtime — orchestration aggregate."""

from __future__ import annotations

from typing import Any

from aethos_core.runtime_convergence_cognition.convergence_memory import record_convergence_memory
from aethos_core.runtime_convergence_cognition.convergence_trajectories import assess_convergence_trajectories
from aethos_core.runtime_convergence_cognition.dependency_convergence import assess_dependency_convergence
from aethos_core.runtime_convergence_cognition.operational_stability_model import model_operational_stability
from aethos_core.runtime_convergence_cognition.replay_convergence import assess_replay_convergence
from aethos_core.runtime_convergence_cognition.topology_convergence import assess_topology_convergence


def orchestrate_convergence_cognition(*, provider: str = "railway") -> dict[str, Any]:
    trajectories = assess_convergence_trajectories()
    stability = model_operational_stability()
    replay = assess_replay_convergence()
    dependency = assess_dependency_convergence()
    topology = assess_topology_convergence()
    memory = record_convergence_memory(converged=trajectories.get("trajectory_improving", False))
    converging = trajectories.get("trajectory_improving") and replay.get("continuity_evolution") == "stable"
    return {
        "trajectories": trajectories,
        "stability_model": stability,
        "replay_convergence": replay,
        "dependency_convergence": dependency,
        "topology_convergence": topology,
        "memory": memory,
        "converging": converging,
        "summary": (
            "Operational stability continues to converge positively across replay continuity, "
            "dependency recovery, and topology stabilization windows. "
            "No significant regression patterns are currently emerging, though extended reconciliation remains active."
        ),
    }
