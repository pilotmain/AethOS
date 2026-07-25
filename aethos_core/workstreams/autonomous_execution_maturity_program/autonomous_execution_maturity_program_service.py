# SPDX-License-Identifier: Apache-2.0
"""PHASE_I1 / FIX 361 — autonomous execution maturity service."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.governance.governance_friction_approval_contract import FIX_361_CERTIFICATION_REQUIREMENTS
from aethos_core.workstreams.autonomous_execution_maturity_program.autonomous_execution_maturity_program_contract import (
    AUTHORITY_EXPANSION_FIX_361,
    AUTONOMOUS_AUTHORITY_FIX_361,
    AUTONOMOUS_EXECUTION_MATURITY_METRICS,
    AUTONOMOUS_EXECUTION_MATURITY_PHASES,
    AUTONOMOUS_EXECUTION_MATURITY_PROGRAM_FIX,
    AUTONOMOUS_EXECUTION_MATURITY_PROGRAM_ID,
    AUTONOMOUS_EXECUTION_MATURITY_PROGRAM_INVARIANT,
    AUTONOMOUS_EXECUTION_MATURITY_PROGRAM_SCHEMA_VERSION,
    AUTONOMOUS_EXECUTION_REQUEST_MIN_SIZE,
    AUTONOMOUS_MATURITY_LEVELS,
    AUTONOMOUS_ORGANIZATIONAL_CONTROL_FIX_361,
    AUTONOMOUS_STRATEGIC_CONTROL_FIX_361,
    CORE_PRINCIPLE,
    EXECUTIVE_WORKSTREAM_MODULES,
    FORBIDDEN_AUTONOMOUS_ACTIONS,
    GOVERNANCE_BYPASS_AUTHORITY_FIX_361,
    GOVERNANCE_BYPASS_FIX_361,
    GOVERNANCE_MUTATION_FIX_361,
    GOVERNANCE_MUTATION_PERFORMED_FIX_361,
    LOCAL_AUTONOMOUS_EXECUTION_MATURITY_EXECUTABLE_FIX_361,
    MUTATION_PERFORMED_FIX_361,
    PROGRAM_NON_GOALS,
    TRUST_MUTATION_AUTHORITY_FIX_361,
    TRUST_PROMOTION_FIX_361,
)
from aethos_core.workstreams.autonomous_execution_maturity_program.autonomous_execution_maturity_program_executor import (
    build_autonomous_capability_registry,
    build_autonomous_execution_registry,
    build_autonomous_learning_report,
    build_execution_planning_accuracy_report,
    build_execution_recovery_report,
    build_execution_success_report,
    build_human_intervention_report,
    compute_autonomous_execution_maturity_metrics,
)
from aethos_core.workstreams.autonomous_execution_maturity_program.autonomous_execution_maturity_program_store import (
    has_autonomous_execution_review_approve,
    list_autonomous_execution_records,
)


@dataclass(frozen=True)
class AutonomousExecutionMaturityProgramResult:
    ok: bool
    session_id: str
    autonomous_execution_maturity_program: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _session_records(records: list[dict[str, Any]], *, session_id: str) -> list[dict[str, Any]]:
    return [r for r in records if str(r.get("session_id") or session_id) == session_id]


def _build_phase_8_executive_visibility(*, program_session_id: str) -> dict[str, Any]:
    metrics = compute_autonomous_execution_maturity_metrics(program_session_id=program_session_id)
    capabilities = build_autonomous_capability_registry(program_session_id=program_session_id)
    return {
        "autonomous_execution_dashboard": {
            "dashboard_id": "autonomous-execution-dashboard",
            "program_session_id": program_session_id,
            "execution_tracks": ["ET1", "ET2", "ET3", "ET4", "ET5"],
            "executive_workstream_modules": list(EXECUTIVE_WORKSTREAM_MODULES),
            "workstream_c1_real_world_delivery_reference": {
                "workstream": "WORKSTREAM_C1",
                "composed_read_only": True,
            },
            "workstream_c2_delivery_optimization_reference": {
                "workstream": "WORKSTREAM_C2",
                "composed_read_only": True,
            },
            "workstream_d1_provider_expansion_reference": {
                "workstream": "WORKSTREAM_D1",
                "composed_read_only": True,
            },
            "workstream_d2_multi_cloud_proof_reference": {
                "workstream": "WORKSTREAM_D2",
                "composed_read_only": True,
            },
            "workstream_f1_customer_delivery_reference": {
                "workstream": "WORKSTREAM_F1",
                "composed_read_only": True,
            },
            "workstream_h3_oversight_reference": {
                "workstream": "WORKSTREAM_H3",
                "composed_read_only": True,
            },
            "autonomous_execution_metrics": metrics,
            "autonomous_maturity_level": metrics.get("autonomous_maturity_level"),
            "proven_capability_count": len(capabilities.get("proven_capabilities") or []),
            "autonomous_authority_granted": False,
            "read_only": True,
        }
    }


def _build_phase_9_human_review(*, program_session_id: str) -> dict[str, Any]:
    records = _session_records(list_autonomous_execution_records(), session_id=program_session_id)
    notes = [r for r in records if str(r.get("kind") or "") == "autonomous_execution_note"]
    decisions = [r for r in records if str(r.get("kind") or "").startswith("autonomous_execution_review_")]
    return {
        "autonomous_execution_review_registry": {
            "registry_id": "autonomous-execution-review-registry",
            "note_count": len(notes),
            "decision_count": len(decisions),
            "notes": notes[-10:],
            "decisions": decisions[-5:],
            "read_only": True,
        }
    }


def _success_criteria(*, program_session_id: str) -> dict[str, Any]:
    registry = build_autonomous_execution_registry(program_session_id=program_session_id)
    planning = build_execution_planning_accuracy_report(program_session_id=program_session_id)
    success = build_execution_success_report(program_session_id=program_session_id)
    recovery = build_execution_recovery_report(program_session_id=program_session_id)
    intervention = build_human_intervention_report(program_session_id=program_session_id)
    learning = build_autonomous_learning_report(program_session_id=program_session_id)
    metrics = compute_autonomous_execution_maturity_metrics(program_session_id=program_session_id)

    return {
        "initiative_monitoring_demonstrated": registry.get("request_count", 0) >= AUTONOMOUS_EXECUTION_REQUEST_MIN_SIZE,
        "planning_accuracy_demonstrated": planning.get("planning_accuracy_demonstrated") is True,
        "execution_success_demonstrated": success.get("execution_success_demonstrated") is True,
        "recovery_analysis_demonstrated": recovery.get("recovery_analysis_demonstrated") is True,
        "human_intervention_analysis_demonstrated": intervention.get("human_intervention_analysis_demonstrated") is True,
        "autonomous_learning_demonstrated": learning.get("autonomous_learning_demonstrated") is True,
        "governed_autonomous_execution_signals": float(metrics.get("autonomous_execution_maturity_score") or 0) >= 0.35,
        "autonomous_authority_granted": False,
        "governance_bypass_performed": False,
        "program_complete": has_autonomous_execution_review_approve(program_session_id=program_session_id),
    }


def build_autonomous_execution_maturity_program(
    *, session_id: str = "default"
) -> AutonomousExecutionMaturityProgramResult:
    sid = (session_id or "default").strip()[:64] or "default"
    blockers: list[str] = []

    sections: dict[str, list[dict[str, Any]]] = {
        "phase_1_autonomous_execution_registry": [
            {"autonomous_execution_registry": build_autonomous_execution_registry(program_session_id=sid)}
        ],
        "phase_2_planning_accuracy_analysis": [
            {"execution_planning_accuracy_report": build_execution_planning_accuracy_report(program_session_id=sid)}
        ],
        "phase_3_execution_success_analysis": [
            {"execution_success_report": build_execution_success_report(program_session_id=sid)}
        ],
        "phase_4_recovery_analysis": [
            {"execution_recovery_report": build_execution_recovery_report(program_session_id=sid)}
        ],
        "phase_5_human_intervention_analysis": [
            {"human_intervention_report": build_human_intervention_report(program_session_id=sid)}
        ],
        "phase_6_autonomous_learning_analysis": [
            {"autonomous_learning_report": build_autonomous_learning_report(program_session_id=sid)}
        ],
        "phase_7_autonomous_capability_registry": [
            {"autonomous_capability_registry": build_autonomous_capability_registry(program_session_id=sid)}
        ],
        "phase_8_executive_visibility": [_build_phase_8_executive_visibility(program_session_id=sid)],
        "phase_9_human_review": [_build_phase_9_human_review(program_session_id=sid)],
    }

    success = _success_criteria(program_session_id=sid)
    metrics = compute_autonomous_execution_maturity_metrics(program_session_id=sid)
    request_count = build_autonomous_execution_registry(program_session_id=sid).get("request_count", 0)

    if request_count < AUTONOMOUS_EXECUTION_REQUEST_MIN_SIZE:
        blockers.append("autonomous_execution_request_minimum_not_met")
    if not has_autonomous_execution_review_approve(program_session_id=sid):
        blockers.append("autonomous_execution_review_approve_required")

    board: dict[str, Any] = {
        "schema_version": AUTONOMOUS_EXECUTION_MATURITY_PROGRAM_SCHEMA_VERSION,
        "phase_id": AUTONOMOUS_EXECUTION_MATURITY_PROGRAM_ID,
        "workstream_id": AUTONOMOUS_EXECUTION_MATURITY_PROGRAM_ID,
        "fix_id": AUTONOMOUS_EXECUTION_MATURITY_PROGRAM_FIX,
        "exported_at": _exported_at(),
        "session_id": sid,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_361,
        "core_principle": CORE_PRINCIPLE,
        "invariant": AUTONOMOUS_EXECUTION_MATURITY_PROGRAM_INVARIANT,
        "forbidden_actions": [f"{key}: {value}" for key, value in FORBIDDEN_AUTONOMOUS_ACTIONS],
        "non_goals": list(PROGRAM_NON_GOALS),
        "phases": list(AUTONOMOUS_EXECUTION_MATURITY_PHASES),
        "autonomous_authority": AUTONOMOUS_AUTHORITY_FIX_361,
        "authority_expansion": AUTHORITY_EXPANSION_FIX_361,
        "governance_mutation": GOVERNANCE_MUTATION_FIX_361,
        "governance_bypass": GOVERNANCE_BYPASS_FIX_361,
        "trust_promotion": TRUST_PROMOTION_FIX_361,
        "autonomous_organizational_control": AUTONOMOUS_ORGANIZATIONAL_CONTROL_FIX_361,
        "autonomous_strategic_control": AUTONOMOUS_STRATEGIC_CONTROL_FIX_361,
        "governance_bypass_authority": GOVERNANCE_BYPASS_AUTHORITY_FIX_361,
        "trust_mutation_authority": TRUST_MUTATION_AUTHORITY_FIX_361,
        "local_autonomous_execution_maturity_executable": LOCAL_AUTONOMOUS_EXECUTION_MATURITY_EXECUTABLE_FIX_361,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_361,
        "autonomous_execution_request_minimum_size": AUTONOMOUS_EXECUTION_REQUEST_MIN_SIZE,
        "autonomous_maturity_levels": list(AUTONOMOUS_MATURITY_LEVELS),
        "metrics_tracked": list(AUTONOMOUS_EXECUTION_MATURITY_METRICS),
        "metrics": metrics,
        "success_criteria": success,
        "composed_from_et1_et5_c1_c2_d1_d2_f1_h3_patterns": True,
        "sections": sections,
        "fix_361_certification_requirements": list(FIX_361_CERTIFICATION_REQUIREMENTS),
    }

    detail = (
        "Autonomous execution maturity program complete"
        if success.get("program_complete")
        else "Autonomous execution maturity composed — human review pending"
    )
    return AutonomousExecutionMaturityProgramResult(
        ok=True,
        session_id=sid,
        autonomous_execution_maturity_program=board,
        blockers=blockers,
        detail=detail,
    )
