# SPDX-License-Identifier: Apache-2.0
"""Long-tail operational memory aggregate."""

from __future__ import annotations

from typing import Any

from aethos_core.long_tail_operational_memory.convergence_memory_runtime import recall_convergence_history
from aethos_core.long_tail_operational_memory.degradation_memory import recall_degradation_memory
from aethos_core.long_tail_operational_memory.provider_operational_memory import recall_provider_operational_memory
from aethos_core.long_tail_operational_memory.recovery_trajectory_memory import record_recovery_trajectory
from aethos_core.long_tail_operational_memory.replay_erosion_memory import recall_replay_erosion
from aethos_core.long_tail_operational_memory.topology_memory import recall_topology_memory


def assess_long_tail_operational_memory(*, provider: str = "railway") -> dict[str, Any]:
    degradation = recall_degradation_memory()
    recovery = record_recovery_trajectory(stage="stabilizing")
    provider_mem = recall_provider_operational_memory(provider=provider)
    replay = recall_replay_erosion()
    topology = recall_topology_memory()
    convergence = recall_convergence_history()
    return {
        "ok": True,
        "degradation_memory": degradation,
        "recovery_trajectory": recovery,
        "provider_memory": provider_mem,
        "replay_erosion": replay,
        "topology_memory": topology,
        "convergence_history": convergence,
        "memory_active": True,
        "summary": "Long-tail operational memory active — infrastructure evolution tracked over time.",
    }
