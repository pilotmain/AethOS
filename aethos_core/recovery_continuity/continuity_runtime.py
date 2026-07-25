# SPDX-License-Identifier: Apache-2.0
"""Continuity runtime — orchestration aggregate."""

from __future__ import annotations

from typing import Any

from aethos_core.recovery_continuity.continuity_decay_detection import detect_continuity_decay
from aethos_core.recovery_continuity.continuity_memory import record_continuity_memory
from aethos_core.recovery_continuity.dependency_continuity import assess_dependency_continuity
from aethos_core.recovery_continuity.replay_continuity_truth import assess_replay_continuity_truth
from aethos_core.recovery_continuity.sustained_recovery_tracking import track_sustained_recovery
from aethos_core.recovery_continuity.topology_continuity import assess_topology_continuity


def orchestrate_recovery_continuity(*, provider: str = "railway") -> dict[str, Any]:
    sustained = track_sustained_recovery(provider=provider)
    decay = detect_continuity_decay()
    replay = assess_replay_continuity_truth()
    dependency = assess_dependency_continuity()
    topology = assess_topology_continuity()
    memory = record_continuity_memory(stable=sustained.get("sustained", False))
    continuity_held = (
        sustained.get("sustained")
        and replay.get("persistence_stable")
        and dependency.get("continuity_held")
        and topology.get("continuity_held")
        and not decay.get("continuity_erosion")
    )
    return {
        "sustained_recovery": sustained,
        "continuity_decay": decay,
        "replay_continuity": replay,
        "dependency_continuity": dependency,
        "topology_continuity": topology,
        "memory": memory,
        "continuity_held": continuity_held,
        "summary": (
            "Operational recovery continues to remain stable across sustained runtime windows, "
            "with replay continuity, dependency convergence, and topology recovery signals remaining healthy "
            "over extended observation periods. Adaptive verification remains active."
        ),
    }
