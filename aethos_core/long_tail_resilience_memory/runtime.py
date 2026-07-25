# SPDX-License-Identifier: Apache-2.0
"""Long-tail resilience memory aggregate."""

from __future__ import annotations

from typing import Any

from aethos_core.long_tail_resilience_memory.degradation_trajectory_memory import recall_degradation_trajectories
from aethos_core.long_tail_resilience_memory.provider_instability_memory import recall_provider_instability
from aethos_core.long_tail_resilience_memory.replay_resilience_memory import recall_replay_resilience_memory
from aethos_core.long_tail_resilience_memory.resilience_journey_memory import recall_resilience_journey
from aethos_core.long_tail_resilience_memory.resilience_pattern_memory import recall_resilience_patterns
from aethos_core.long_tail_resilience_memory.topology_fragility_memory import recall_topology_fragility_memory


def assess_long_tail_resilience_memory(*, provider: str = "railway") -> dict[str, Any]:
    patterns = recall_resilience_patterns()
    trajectories = recall_degradation_trajectories()
    provider_mem = recall_provider_instability(provider=provider)
    replay = recall_replay_resilience_memory()
    topology = recall_topology_fragility_memory()
    journey = recall_resilience_journey()
    return {
        "ok": True,
        "resilience_patterns": patterns,
        "degradation_trajectories": trajectories,
        "provider_instability": provider_mem,
        "replay_resilience": replay,
        "topology_fragility": topology,
        "resilience_journey": journey,
        "memory_active": True,
        "summary": "Long-tail resilience memory active — recovery durability patterns tracked over time.",
    }
