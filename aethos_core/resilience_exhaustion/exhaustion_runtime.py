# SPDX-License-Identifier: Apache-2.0
"""Exhaustion runtime — exhaustion orchestration."""

from __future__ import annotations

from typing import Any

from aethos_core.resilience_exhaustion.exhaustion_memory import record_exhaustion_memory
from aethos_core.resilience_exhaustion.operational_endurance_decay import assess_operational_endurance_decay
from aethos_core.resilience_exhaustion.replay_exhaustion import assess_replay_exhaustion
from aethos_core.resilience_exhaustion.stabilization_exhaustion import assess_stabilization_exhaustion
from aethos_core.resilience_exhaustion.survivability_decay import assess_survivability_decay


def orchestrate_resilience_exhaustion() -> dict[str, Any]:
    replay = assess_replay_exhaustion()
    stabilization = assess_stabilization_exhaustion()
    endurance = assess_operational_endurance_decay()
    survivability = assess_survivability_decay()
    memory = record_exhaustion_memory(stable=not endurance.get("endurance_weakening", False))
    exhaustion_emerging = (
        replay.get("exhaustion_emerging")
        or stabilization.get("exhaustion_emerging")
        or endurance.get("endurance_weakening")
        or survivability.get("decay_emerging")
    )
    return {
        "replay_exhaustion": replay,
        "stabilization_exhaustion": stabilization,
        "operational_endurance_decay": endurance,
        "survivability_decay": survivability,
        "memory": memory,
        "exhaustion_emerging": exhaustion_emerging,
        "summary": stabilization.get("summary", "Resilience exhaustion cognition active."),
    }
