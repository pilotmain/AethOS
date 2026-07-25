# SPDX-License-Identifier: Apache-2.0
"""Infrastructure fragility aggregate."""

from __future__ import annotations

from typing import Any

from aethos_core.infrastructure_fragility.fragility_memory import record_fragility_memory
from aethos_core.infrastructure_fragility.operational_erosion_patterns import detect_operational_erosion_patterns
from aethos_core.infrastructure_fragility.provider_fragility import assess_provider_fragility
from aethos_core.infrastructure_fragility.recovery_asymmetry import detect_recovery_asymmetry
from aethos_core.infrastructure_fragility.replay_fragility import assess_replay_fragility
from aethos_core.infrastructure_fragility.topology_fragility_runtime import assess_topology_fragility_runtime


def assess_infrastructure_fragility(*, provider: str = "railway") -> dict[str, Any]:
    topology = assess_topology_fragility_runtime()
    replay = assess_replay_fragility()
    provider_f = assess_provider_fragility(provider=provider)
    asymmetry = detect_recovery_asymmetry()
    erosion = detect_operational_erosion_patterns()
    memory = record_fragility_memory(zone="topology_edge")
    fragile = topology.get("fragile") or replay.get("fragile") or asymmetry.get("asymmetric")
    return {
        "ok": True,
        "topology_fragility": topology,
        "replay_fragility": replay,
        "provider_fragility": provider_f,
        "recovery_asymmetry": asymmetry,
        "erosion_patterns": erosion,
        "fragility_memory": memory,
        "fragility_elevated": fragile,
        "summary": "Infrastructure fragility intelligence active — resistance to future instability monitored.",
    }
