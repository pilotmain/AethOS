# SPDX-License-Identifier: Apache-2.0
"""Survivability runtime — orchestration aggregate."""

from __future__ import annotations

from typing import Any

from aethos_core.operational_survivability.dependency_survivability import assess_dependency_survivability
from aethos_core.operational_survivability.recovery_survivability import assess_recovery_survivability
from aethos_core.operational_survivability.replay_survivability import assess_replay_survivability
from aethos_core.operational_survivability.survivability_memory import record_survivability_memory
from aethos_core.operational_survivability.topology_survivability import assess_topology_survivability


def orchestrate_operational_survivability() -> dict[str, Any]:
    recovery = assess_recovery_survivability()
    topology = assess_topology_survivability()
    dependency = assess_dependency_survivability()
    replay = assess_replay_survivability()
    memory = record_survivability_memory()
    survivable = recovery.get("survivable") and dependency.get("survivable") and replay.get("longevity_stable")
    return {
        "recovery_survivability": recovery,
        "topology_survivability": topology,
        "dependency_survivability": dependency,
        "replay_survivability": replay,
        "memory": memory,
        "survivable": survivable,
        "summary": "Operational survivability cognition active — long-term durability evaluated.",
    }
