# SPDX-License-Identifier: Apache-2.0
"""Fragility runtime — orchestration aggregate."""

from __future__ import annotations

from typing import Any

from aethos_core.runtime_fragility.fragility_memory import record_runtime_fragility_memory
from aethos_core.runtime_fragility.provider_fragility import detect_provider_fragility
from aethos_core.runtime_fragility.recovery_fragility import assess_recovery_fragility
from aethos_core.runtime_fragility.replay_fragility import detect_replay_fragility
from aethos_core.runtime_fragility.topology_fragility import detect_topology_fragility


def orchestrate_runtime_fragility(*, provider: str = "railway") -> dict[str, Any]:
    replay = detect_replay_fragility()
    topology = detect_topology_fragility()
    provider_f = detect_provider_fragility(provider=provider)
    recovery = assess_recovery_fragility()
    memory = record_runtime_fragility_memory()
    fragile = replay.get("fragile") or topology.get("fragile") or recovery.get("unstable")
    return {
        "replay_fragility": replay,
        "topology_fragility": topology,
        "provider_fragility": provider_f,
        "recovery_fragility": recovery,
        "fragility_memory": memory,
        "fragility_elevated": fragile,
        "summary": "Runtime fragility intelligence active — recovery durability under stress monitored.",
    }
