# SPDX-License-Identifier: Apache-2.0
"""Acceleration runtime — orchestration aggregate."""

from __future__ import annotations

from typing import Any

from aethos_core.degradation_acceleration.acceleration_memory import record_degradation_acceleration_memory
from aethos_core.degradation_acceleration.provider_acceleration import measure_provider_acceleration
from aethos_core.degradation_acceleration.recovery_acceleration import measure_recovery_acceleration
from aethos_core.degradation_acceleration.replay_acceleration import measure_replay_acceleration
from aethos_core.degradation_acceleration.topology_acceleration import measure_topology_acceleration
from aethos_core.fragility_acceleration.fatigue_acceleration import detect_fatigue_acceleration


def orchestrate_degradation_acceleration(*, provider: str = "railway") -> dict[str, Any]:
    replay = measure_replay_acceleration()
    topology = measure_topology_acceleration()
    provider_a = measure_provider_acceleration(provider=provider)
    recovery = measure_recovery_acceleration()
    strain = detect_fatigue_acceleration(fatigue_score=0.32)
    memory = record_degradation_acceleration_memory()
    accelerating = replay.get("accelerating") or topology.get("accelerating") or recovery.get("accelerating")
    return {
        "replay_acceleration": replay,
        "topology_acceleration": topology,
        "provider_acceleration": provider_a,
        "recovery_acceleration": recovery,
        "operational_strain": strain,
        "memory": memory,
        "acceleration_detected": accelerating,
        "summary": "Degradation acceleration intelligence active — silent acceleration monitored over time.",
    }
