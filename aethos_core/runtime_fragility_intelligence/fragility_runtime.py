# SPDX-License-Identifier: Apache-2.0
"""Fragility runtime — orchestration aggregate."""

from __future__ import annotations

from typing import Any

from aethos_core.runtime_fragility_intelligence.fragility_memory import record_fragility_history
from aethos_core.runtime_fragility_intelligence.instability_trajectories import track_instability_trajectories
from aethos_core.runtime_fragility_intelligence.replay_fragility_projection import project_replay_fragility
from aethos_core.runtime_fragility_intelligence.resilience_decay import assess_resilience_decay
from aethos_core.runtime_fragility_intelligence.topology_fragility_projection import project_topology_fragility


def orchestrate_runtime_fragility(*, provider: str = "railway") -> dict[str, Any]:
    trajectories = track_instability_trajectories()
    decay = assess_resilience_decay()
    replay = project_replay_fragility()
    topology = project_topology_fragility()
    memory = record_fragility_history()
    fragile_emerging = decay.get("weakening") or not topology.get("moderate_signals")
    return {
        "instability_trajectories": trajectories,
        "resilience_decay": decay,
        "replay_fragility": replay,
        "topology_fragility": topology,
        "memory": memory,
        "fragility_emerging": fragile_emerging,
        "summary": (
            "Operational recovery continues to remain resilient across sustained runtime pressure, "
            "though moderate replay erosion and topology fragility signals are beginning to emerge across extended operational verification windows. "
            "No critical instability acceleration patterns are currently emerging."
        ),
    }
