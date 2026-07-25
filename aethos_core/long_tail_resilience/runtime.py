# SPDX-License-Identifier: Apache-2.0
"""Long-tail resilience aggregate."""

from __future__ import annotations

from typing import Any

from aethos_core.long_tail_resilience.degradation_evolution import track_degradation_evolution
from aethos_core.long_tail_resilience.provider_instability_memory import recall_provider_degradation
from aethos_core.long_tail_resilience.replay_resilience_memory import recall_replay_durability
from aethos_core.long_tail_resilience.resilience_journey_memory import recall_operational_evolution
from aethos_core.long_tail_resilience.resilience_patterns import recall_resilience_patterns_long_tail
from aethos_core.long_tail_resilience.topology_fragility_memory import recall_topology_weak_points


def assess_long_tail_resilience(*, provider: str = "railway") -> dict[str, Any]:
    patterns = recall_resilience_patterns_long_tail()
    degradation = track_degradation_evolution()
    provider_mem = recall_provider_degradation(provider=provider)
    replay = recall_replay_durability()
    topology = recall_topology_weak_points()
    journey = recall_operational_evolution()
    return {
        "ok": True,
        "resilience_patterns": patterns,
        "degradation_evolution": degradation,
        "provider_instability": provider_mem,
        "replay_resilience": replay,
        "topology_fragility": topology,
        "resilience_journey": journey,
        "memory_active": True,
        "summary": "Long-tail resilience memory active — recovery patterns tracked for durability over time.",
    }
