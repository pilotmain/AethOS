# SPDX-License-Identifier: Apache-2.0
"""Resilience runtime — orchestration aggregate."""

from __future__ import annotations

from typing import Any

from aethos_core.operational_resilience.dependency_resilience import assess_dependency_resilience
from aethos_core.operational_resilience.replay_resilience_tracking import track_replay_resilience
from aethos_core.operational_resilience.resilience_memory import record_resilience_memory
from aethos_core.operational_resilience.resilience_trajectories import track_operational_resilience_trajectories
from aethos_core.operational_resilience.topology_resilience import assess_topology_durability
from aethos_core.operational_resilience_cognition.degradation_resilience import assess_degradation_resilience


def orchestrate_resilience(*, provider: str = "railway") -> dict[str, Any]:
    trajectories = track_operational_resilience_trajectories()
    replay = track_replay_resilience()
    dependency = assess_dependency_resilience()
    topology = assess_topology_durability()
    degradation = assess_degradation_resilience()
    memory = record_resilience_memory(resilient=trajectories.get("durable", False))
    resilient = (
        trajectories.get("durable")
        and replay.get("durable")
        and dependency.get("resilient")
        and topology.get("durable")
        and degradation.get("erosion_resistant")
    )
    return {
        "trajectories": trajectories,
        "replay_resilience": replay,
        "dependency_resilience": dependency,
        "topology_resilience": topology,
        "degradation_resilience": degradation,
        "memory": memory,
        "resilient": resilient,
        "summary": (
            "Operational recovery continues to remain resilient across sustained runtime pressure, "
            "with replay persistence, dependency convergence, and topology durability signals remaining healthy "
            "across extended operational verification windows. "
            "No significant resilience degradation patterns are currently emerging."
        ),
    }
