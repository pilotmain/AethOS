# SPDX-License-Identifier: Apache-2.0
"""Acceleration runtime — orchestration aggregate."""

from __future__ import annotations

from typing import Any

from aethos_core.fragility_acceleration.acceleration_memory import record_acceleration_memory
from aethos_core.fragility_acceleration.fatigue_acceleration import detect_fatigue_acceleration
from aethos_core.fragility_acceleration.provider_acceleration import detect_provider_acceleration
from aethos_core.fragility_acceleration.replay_acceleration import detect_replay_acceleration
from aethos_core.fragility_acceleration.topology_acceleration import detect_topology_acceleration


def orchestrate_fragility_acceleration(*, provider: str = "railway") -> dict[str, Any]:
    replay = detect_replay_acceleration()
    topology = detect_topology_acceleration()
    provider_a = detect_provider_acceleration(provider=provider)
    fatigue = detect_fatigue_acceleration()
    memory = record_acceleration_memory()
    accelerating = replay.get("accelerating") or topology.get("accelerating") or fatigue.get("accelerating")
    return {
        "replay_acceleration": replay,
        "topology_acceleration": topology,
        "provider_acceleration": provider_a,
        "fatigue_acceleration": fatigue,
        "memory": memory,
        "acceleration_detected": accelerating,
        "summary": "Fragility acceleration intelligence active — degradation acceleration monitored silently over time.",
    }
