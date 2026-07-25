# SPDX-License-Identifier: Apache-2.0
"""Reliability memory orchestrator."""

from __future__ import annotations

from typing import Any

from aethos_core.reliability_memory.confidence_history import confidence_history_state, record_confidence_snapshot
from aethos_core.reliability_memory.degradation_memory import degradation_memory_state, record_degradation_pathway
from aethos_core.reliability_memory.incident_history import incident_history_state, record_incident
from aethos_core.reliability_memory.infrastructure_journey import infrastructure_journey_state, record_journey_milestone
from aethos_core.reliability_memory.recovery_history import recovery_history_state
from aethos_core.reliability_memory.replay_memory import record_replay_event, replay_memory_state


def assess_reliability_memory(*, runtime_snapshot: dict[str, Any] | None = None) -> dict[str, Any]:
    from aethos_core.drift_intelligence.runtime import assess_drift_intelligence

    drift = assess_drift_intelligence(runtime_snapshot=runtime_snapshot)
    if drift.get("replay", {}).get("replay_continuity_degraded"):
        record_replay_event(entry={"type": "continuity_degradation", "source": "drift_intelligence"})
    if drift.get("degradation", {}).get("degradation_detected"):
        for svc in drift.get("degradation", {}).get("unstable_workloads") or []:
            record_degradation_pathway(pathway="restart_loop", service=str(svc))
            record_incident(entry={"service": svc, "type": "degradation"})
    record_journey_milestone(milestone={"phase": "11.3", "drift_bounded": drift.get("drift_bounded")})
    return {
        "ok": True,
        "incidents": incident_history_state(),
        "recovery": recovery_history_state(),
        "degradation": degradation_memory_state(),
        "journey": infrastructure_journey_state(),
        "confidence": confidence_history_state(),
        "replay": replay_memory_state(),
        "summary": "Operational reliability history continuity maintained.",
    }
