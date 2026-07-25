# SPDX-License-Identifier: Apache-2.0
"""Infrastructure intuition aggregate."""

from __future__ import annotations

from typing import Any

from aethos_core.infrastructure_intuition.degradation_signatures import detect_degradation_signatures
from aethos_core.infrastructure_intuition.infrastructure_journey import describe_infrastructure_journey
from aethos_core.infrastructure_intuition.operational_pattern_memory import remember_operational_pattern
from aethos_core.infrastructure_intuition.provider_behavior_memory import recall_provider_behavior
from aethos_core.infrastructure_intuition.replay_instability_memory import record_replay_instability
from aethos_core.infrastructure_intuition.topology_fragility import detect_topology_fragility


def assess_infrastructure_intuition(*, provider: str = "railway") -> dict[str, Any]:
    signatures = detect_degradation_signatures()
    provider_memory = recall_provider_behavior(provider=provider)
    fragility = detect_topology_fragility()
    replay_memory = record_replay_instability(stable=True)
    patterns = remember_operational_pattern(pattern="sustained_convergence")
    journey = describe_infrastructure_journey()
    return {
        "ok": True,
        "degradation_signatures": signatures,
        "provider_behavior": provider_memory,
        "topology_fragility": fragility,
        "replay_instability_memory": replay_memory,
        "operational_patterns": patterns,
        "infrastructure_journey": journey,
        "intuition_active": not fragility.get("fragile"),
        "summary": "Infrastructure intuition active — operational memory informing convergence cognition.",
    }
