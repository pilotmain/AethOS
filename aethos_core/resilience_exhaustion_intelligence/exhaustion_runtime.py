# SPDX-License-Identifier: Apache-2.0
"""Exhaustion runtime — exhaustion orchestration."""

from __future__ import annotations

from typing import Any

from aethos_core.resilience_exhaustion_intelligence.exhaustion_memory import record_exhaustion_memory
from aethos_core.resilience_exhaustion_intelligence.recovery_exhaustion_projection import project_recovery_exhaustion
from aethos_core.resilience_exhaustion_intelligence.replay_exhaustion_projection import project_replay_exhaustion
from aethos_core.resilience_exhaustion_intelligence.stabilization_endurance_decay import assess_stabilization_endurance_decay
from aethos_core.resilience_exhaustion_intelligence.survivability_exhaustion import assess_survivability_exhaustion


def orchestrate_resilience_exhaustion_intelligence() -> dict[str, Any]:
    replay = project_replay_exhaustion()
    stabilization = assess_stabilization_endurance_decay()
    survivability = assess_survivability_exhaustion()
    recovery = project_recovery_exhaustion()
    memory = record_exhaustion_memory(stable=not survivability.get("exhaustion_emerging", False))
    exhaustion_emerging = (
        replay.get("exhaustion_emerging")
        or stabilization.get("decay_emerging")
        or survivability.get("exhaustion_emerging")
        or recovery.get("exhaustion_emerging")
    )
    return {
        "replay_exhaustion": replay,
        "stabilization_endurance_decay": stabilization,
        "survivability_exhaustion": survivability,
        "recovery_exhaustion": recovery,
        "memory": memory,
        "exhaustion_emerging": exhaustion_emerging,
        "summary": stabilization.get("summary", "Resilience exhaustion intelligence active."),
    }
