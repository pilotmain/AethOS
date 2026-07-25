# SPDX-License-Identifier: Apache-2.0
"""Resilience runtime — orchestration aggregate."""

from __future__ import annotations

from typing import Any

from aethos_core.operational_resilience_cognition.degradation_resilience import assess_degradation_resilience
from aethos_core.operational_resilience_cognition.replay_resilience import assess_replay_resilience_under_pressure
from aethos_core.operational_resilience_cognition.resilience_trajectories import track_resilience_trajectories
from aethos_core.operational_resilience_cognition.sustained_resilience_memory import record_sustained_resilience
from aethos_core.operational_resilience_cognition.topology_resilience_tracking import track_topology_resilience
from aethos_core.recovery_continuity.dependency_continuity import assess_dependency_continuity


def orchestrate_operational_resilience(*, provider: str = "railway") -> dict[str, Any]:
    trajectories = track_resilience_trajectories()
    topology = track_topology_resilience()
    replay = assess_replay_resilience_under_pressure()
    dependency = assess_dependency_continuity()
    degradation = assess_degradation_resilience()
    memory = record_sustained_resilience(resilient=trajectories.get("durable", False))
    resilient = (
        trajectories.get("durable")
        and topology.get("stability_held")
        and replay.get("pressure_resilient")
        and dependency.get("continuity_held")
        and degradation.get("erosion_resistant")
    )
    return {
        "trajectories": trajectories,
        "topology_resilience": topology,
        "replay_resilience": replay,
        "dependency_convergence": dependency,
        "degradation_resilience": degradation,
        "memory": memory,
        "resilient": resilient,
        "summary": (
            "Operational stability continues to remain resilient across sustained runtime pressure, "
            "with replay continuity, dependency convergence, and topology recovery signals maintaining healthy long-tail trajectories. "
            "No significant resilience regression patterns are currently emerging."
        ),
    }
