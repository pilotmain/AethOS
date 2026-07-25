# SPDX-License-Identifier: Apache-2.0
"""Survivability runtime — orchestration aggregate."""

from __future__ import annotations

from typing import Any

from aethos_core.runtime_survivability_intelligence.recovery_durability_projection import project_recovery_durability
from aethos_core.runtime_survivability_intelligence.replay_survivability_projection import project_replay_survivability
from aethos_core.runtime_survivability_intelligence.runtime_survivability_projection import project_runtime_survivability
from aethos_core.runtime_survivability_intelligence.survivability_memory import record_survivability_memory
from aethos_core.runtime_survivability_intelligence.topology_survivability_projection import project_topology_survivability


def orchestrate_runtime_survivability(*, provider: str = "railway") -> dict[str, Any]:
    runtime = project_runtime_survivability()
    recovery = project_recovery_durability()
    replay = project_replay_survivability()
    topology = project_topology_survivability()
    memory = record_survivability_memory()
    survivable = (
        runtime.get("survivable")
        and recovery.get("durable")
        and replay.get("continuity_sustainable")
        and topology.get("endurance_stable")
    )
    return {
        "runtime_survivability": runtime,
        "recovery_durability": recovery,
        "replay_survivability": replay,
        "topology_survivability": topology,
        "memory": memory,
        "survivable": survivable,
        "summary": "Runtime survivability intelligence active — long-term durability evaluated.",
    }
