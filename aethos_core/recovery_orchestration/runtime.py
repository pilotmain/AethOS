# SPDX-License-Identifier: Apache-2.0
"""Recovery orchestration orchestrator."""

from __future__ import annotations

from typing import Any

from aethos_core.recovery_orchestration.degraded_pathways import identify_degraded_pathways
from aethos_core.recovery_orchestration.dependency_recovery import plan_dependency_recovery
from aethos_core.recovery_orchestration.escalation_runtime import assess_escalation
from aethos_core.recovery_orchestration.recovery_memory import record_recovery_pattern, recovery_memory_state
from aethos_core.recovery_orchestration.recovery_planner import plan_recovery_sequence
from aethos_core.recovery_orchestration.stabilization_windows import define_stabilization_windows
from aethos_core.infrastructure_intelligence.runtime import assess_infrastructure_state


def orchestrate_recovery(*, runtime_snapshot: dict[str, Any] | None = None) -> dict[str, Any]:
    infrastructure = assess_infrastructure_state(runtime_snapshot=runtime_snapshot)
    topology = infrastructure.get("topology") or {}
    supervision = infrastructure.get("supervision") or {}
    degraded = supervision.get("restart_patterns", {}).get("unstable_workloads") or []
    plan = plan_recovery_sequence(topology=topology, degraded=degraded)
    dependency = plan_dependency_recovery(topology=topology, plan=plan)
    windows = define_stabilization_windows()
    loops = supervision.get("restart_patterns", {}).get("restart_loops_detected", 0)
    decay = {"verification_decay": min(0.3, loops * 0.1)}
    escalation = assess_escalation(decay=decay, restart_loops=loops)
    pathways = identify_degraded_pathways(escalation=escalation)
    coordinated = len(plan.get("stages") or []) > 0 and not escalation.get("escalate")
    record_recovery_pattern(entry={"degraded": degraded, "escalation": escalation.get("escalation_level")})
    summary = _build_summary(coordinated, plan, dependency)
    return {
        "ok": True,
        "coordinated": coordinated,
        "maturity": "stable" if coordinated else "beta",
        "plan": plan,
        "dependency_recovery": dependency,
        "windows": windows,
        "escalation": escalation,
        "pathways": pathways,
        "memory": recovery_memory_state(),
        "principle": "Recovery is not a restart action. Recovery is the restoration of operational stability across dependencies.",
        "summary": summary,
    }


def _build_summary(coordinated: bool, plan: dict[str, Any], dependency: dict[str, Any]) -> str:
    if not coordinated:
        return "Recovery orchestration active — staged stabilization sequencing in progress across dependencies."
    return (
        f"Recovery orchestration coordinated: {plan.get('stage_count', 0)} stages planned. "
        f"{dependency.get('summary', '')} Extended stabilization windows remain active."
    )
