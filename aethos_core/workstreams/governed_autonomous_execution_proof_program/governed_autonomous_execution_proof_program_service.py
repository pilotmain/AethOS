# SPDX-License-Identifier: Apache-2.0
"""PHASE_I2 / FIX 362 — governed autonomous execution proof service."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.governance.governance_friction_approval_contract import FIX_362_CERTIFICATION_REQUIREMENTS
from aethos_core.workstreams.governed_autonomous_execution_proof_program.governed_autonomous_execution_proof_program_contract import (
    APPROVAL_BYPASS_FIX_362,
    AUTHORITY_EXPANSION_FIX_362,
    AUTONOMOUS_AUTHORITY_FIX_362,
    AUTONOMOUS_EXECUTION_PROOF_METRICS,
    AUTONOMOUS_PROOF_LEVELS,
    AUTONOMOUS_PROOF_REPEAT_MIN_SIZE,
    AUTONOMOUS_PROOF_RUN_MIN_SIZE,
    CORE_PRINCIPLE,
    EXECUTIVE_WORKSTREAM_MODULES,
    FORBIDDEN_AUTONOMOUS_PROOF_ACTIONS,
    GOVERNANCE_BYPASS_AUTHORITY_FIX_362,
    GOVERNANCE_BYPASS_FIX_362,
    GOVERNANCE_MUTATION_FIX_362,
    GOVERNANCE_MUTATION_PERFORMED_FIX_362,
    GOVERNED_AUTONOMOUS_EXECUTION_PROOF_PHASES,
    GOVERNED_AUTONOMOUS_EXECUTION_PROOF_PROGRAM_FIX,
    GOVERNED_AUTONOMOUS_EXECUTION_PROOF_PROGRAM_ID,
    GOVERNED_AUTONOMOUS_EXECUTION_PROOF_PROGRAM_INVARIANT,
    GOVERNED_AUTONOMOUS_EXECUTION_PROOF_PROGRAM_SCHEMA_VERSION,
    LOCAL_GOVERNED_AUTONOMOUS_EXECUTION_PROOF_EXECUTABLE_FIX_362,
    MUTATION_PERFORMED_FIX_362,
    PROGRAM_NON_GOALS,
    TRUST_MUTATION_AUTHORITY_FIX_362,
    TRUST_PROMOTION_FIX_362,
)
from aethos_core.workstreams.governed_autonomous_execution_proof_program.governed_autonomous_execution_proof_program_executor import (
    build_autonomous_capability_proof_report,
    build_autonomous_consistency_report,
    build_autonomous_intervention_trend_report,
    build_autonomous_proof_opportunity_registry,
    build_autonomous_recovery_evidence_report,
    build_autonomous_run_registry,
    build_autonomous_success_evidence_report,
    compute_autonomous_execution_proof_metrics,
)
from aethos_core.workstreams.governed_autonomous_execution_proof_program.governed_autonomous_execution_proof_program_store import (
    has_autonomous_proof_review_approve,
    list_autonomous_proof_records,
)


@dataclass(frozen=True)
class GovernedAutonomousExecutionProofProgramResult:
    ok: bool
    session_id: str
    governed_autonomous_execution_proof_program: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _session_records(records: list[dict[str, Any]], *, session_id: str) -> list[dict[str, Any]]:
    return [r for r in records if str(r.get("session_id") or session_id) == session_id]


def _build_phase_8_executive_visibility(*, program_session_id: str) -> dict[str, Any]:
    metrics = compute_autonomous_execution_proof_metrics(program_session_id=program_session_id)
    capabilities = build_autonomous_capability_proof_report(program_session_id=program_session_id)
    return {
        "autonomous_execution_proof_dashboard": {
            "dashboard_id": "autonomous-execution-proof-dashboard",
            "program_session_id": program_session_id,
            "execution_tracks": ["ET1", "ET2", "ET3", "ET4", "ET5"],
            "executive_workstream_modules": list(EXECUTIVE_WORKSTREAM_MODULES),
            "phase_i1_autonomous_execution_maturity_reference": {
                "phase": "PHASE_I1",
                "composed_read_only": True,
            },
            "workstream_c1_real_world_delivery_reference": {
                "workstream": "WORKSTREAM_C1",
                "composed_read_only": True,
            },
            "workstream_c2_delivery_optimization_reference": {
                "workstream": "WORKSTREAM_C2",
                "composed_read_only": True,
            },
            "workstream_d2_multi_cloud_proof_reference": {
                "workstream": "WORKSTREAM_D2",
                "composed_read_only": True,
            },
            "workstream_f1_f7_customer_business_validation_reference": {
                "workstreams": [
                    "WORKSTREAM_F1",
                    "WORKSTREAM_F2",
                    "WORKSTREAM_F3",
                    "WORKSTREAM_F4",
                    "WORKSTREAM_F5",
                    "WORKSTREAM_F6",
                    "WORKSTREAM_F7",
                ],
                "composed_read_only": True,
            },
            "workstream_g4_enterprise_readiness_reference": {
                "workstream": "WORKSTREAM_G4",
                "composed_read_only": True,
            },
            "workstream_h3_oversight_reference": {
                "workstream": "WORKSTREAM_H3",
                "composed_read_only": True,
            },
            "autonomous_execution_proof_metrics": metrics,
            "autonomous_proof_level": metrics.get("autonomous_proof_level"),
            "proven_capability_count": len(capabilities.get("proven_capabilities") or []),
            "autonomous_authority_granted": False,
            "read_only": True,
        }
    }


def _build_phase_9_human_review(*, program_session_id: str) -> dict[str, Any]:
    records = _session_records(list_autonomous_proof_records(), session_id=program_session_id)
    notes = [r for r in records if str(r.get("kind") or "") == "autonomous_proof_note"]
    decisions = [r for r in records if str(r.get("kind") or "").startswith("autonomous_proof_review_")]
    return {
        "autonomous_execution_proof_review_registry": {
            "registry_id": "autonomous-execution-proof-review-registry",
            "note_count": len(notes),
            "decision_count": len(decisions),
            "notes": notes[-10:],
            "decisions": decisions[-5:],
            "read_only": True,
        }
    }


def _success_criteria(*, program_session_id: str) -> dict[str, Any]:
    registry = build_autonomous_run_registry(program_session_id=program_session_id)
    success = build_autonomous_success_evidence_report(program_session_id=program_session_id)
    recovery = build_autonomous_recovery_evidence_report(program_session_id=program_session_id)
    intervention = build_autonomous_intervention_trend_report(program_session_id=program_session_id)
    consistency = build_autonomous_consistency_report(program_session_id=program_session_id)
    metrics = compute_autonomous_execution_proof_metrics(program_session_id=program_session_id)

    return {
        "autonomous_run_registry_demonstrated": registry.get("run_count", 0) >= AUTONOMOUS_PROOF_RUN_MIN_SIZE,
        "repeated_success_demonstrated": success.get("repeated_success_demonstrated") is True,
        "repeated_recovery_demonstrated": recovery.get("repeated_recovery_demonstrated") is True,
        "reduced_intervention_demonstrated": intervention.get("reduced_intervention_demonstrated") is True,
        "verified_outcomes_demonstrated": int(success.get("verified_executions") or 0) >= 1,
        "operational_consistency_demonstrated": consistency.get("operational_consistency_demonstrated") is True,
        "governed_autonomous_execution_proof_signals": float(metrics.get("autonomous_execution_proof_score") or 0) >= 0.35,
        "autonomous_authority_granted": False,
        "approval_bypass_performed": False,
        "program_complete": has_autonomous_proof_review_approve(program_session_id=program_session_id),
    }


def build_governed_autonomous_execution_proof_program(
    *, session_id: str = "default"
) -> GovernedAutonomousExecutionProofProgramResult:
    sid = (session_id or "default").strip()[:64] or "default"
    blockers: list[str] = []

    sections: dict[str, list[dict[str, Any]]] = {
        "phase_1_autonomous_run_registry": [
            {"autonomous_run_registry": build_autonomous_run_registry(program_session_id=sid)}
        ],
        "phase_2_success_evidence_analysis": [
            {"autonomous_success_evidence_report": build_autonomous_success_evidence_report(program_session_id=sid)}
        ],
        "phase_3_recovery_evidence_analysis": [
            {"autonomous_recovery_evidence_report": build_autonomous_recovery_evidence_report(program_session_id=sid)}
        ],
        "phase_4_human_intervention_trend_analysis": [
            {"autonomous_intervention_trend_report": build_autonomous_intervention_trend_report(program_session_id=sid)}
        ],
        "phase_5_capability_proof_analysis": [
            {"autonomous_capability_proof_report": build_autonomous_capability_proof_report(program_session_id=sid)}
        ],
        "phase_6_operational_consistency_analysis": [
            {"autonomous_consistency_report": build_autonomous_consistency_report(program_session_id=sid)}
        ],
        "phase_7_proof_opportunity_registry": [
            {"autonomous_proof_opportunity_registry": build_autonomous_proof_opportunity_registry(program_session_id=sid)}
        ],
        "phase_8_executive_visibility": [_build_phase_8_executive_visibility(program_session_id=sid)],
        "phase_9_human_review": [_build_phase_9_human_review(program_session_id=sid)],
    }

    success = _success_criteria(program_session_id=sid)
    metrics = compute_autonomous_execution_proof_metrics(program_session_id=sid)
    run_count = build_autonomous_run_registry(program_session_id=sid).get("run_count", 0)

    if run_count < AUTONOMOUS_PROOF_RUN_MIN_SIZE:
        blockers.append("autonomous_proof_run_minimum_not_met")
    if not has_autonomous_proof_review_approve(program_session_id=sid):
        blockers.append("autonomous_proof_review_approve_required")

    board: dict[str, Any] = {
        "schema_version": GOVERNED_AUTONOMOUS_EXECUTION_PROOF_PROGRAM_SCHEMA_VERSION,
        "phase_id": GOVERNED_AUTONOMOUS_EXECUTION_PROOF_PROGRAM_ID,
        "workstream_id": GOVERNED_AUTONOMOUS_EXECUTION_PROOF_PROGRAM_ID,
        "fix_id": GOVERNED_AUTONOMOUS_EXECUTION_PROOF_PROGRAM_FIX,
        "exported_at": _exported_at(),
        "session_id": sid,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_362,
        "core_principle": CORE_PRINCIPLE,
        "invariant": GOVERNED_AUTONOMOUS_EXECUTION_PROOF_PROGRAM_INVARIANT,
        "forbidden_actions": [f"{key}: {value}" for key, value in FORBIDDEN_AUTONOMOUS_PROOF_ACTIONS],
        "non_goals": list(PROGRAM_NON_GOALS),
        "phases": list(GOVERNED_AUTONOMOUS_EXECUTION_PROOF_PHASES),
        "autonomous_authority": AUTONOMOUS_AUTHORITY_FIX_362,
        "authority_expansion": AUTHORITY_EXPANSION_FIX_362,
        "governance_mutation": GOVERNANCE_MUTATION_FIX_362,
        "governance_bypass": GOVERNANCE_BYPASS_FIX_362,
        "trust_promotion": TRUST_PROMOTION_FIX_362,
        "approval_bypass": APPROVAL_BYPASS_FIX_362,
        "governance_bypass_authority": GOVERNANCE_BYPASS_AUTHORITY_FIX_362,
        "trust_mutation_authority": TRUST_MUTATION_AUTHORITY_FIX_362,
        "local_governed_autonomous_execution_proof_executable": LOCAL_GOVERNED_AUTONOMOUS_EXECUTION_PROOF_EXECUTABLE_FIX_362,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_362,
        "autonomous_proof_run_minimum_size": AUTONOMOUS_PROOF_RUN_MIN_SIZE,
        "autonomous_proof_repeat_minimum_size": AUTONOMOUS_PROOF_REPEAT_MIN_SIZE,
        "autonomous_proof_levels": list(AUTONOMOUS_PROOF_LEVELS),
        "metrics_tracked": list(AUTONOMOUS_EXECUTION_PROOF_METRICS),
        "metrics": metrics,
        "success_criteria": success,
        "composed_from_phase_i1_et1_et5_c1_c2_d2_f1_f7_g4_h3_patterns": True,
        "sections": sections,
        "fix_362_certification_requirements": list(FIX_362_CERTIFICATION_REQUIREMENTS),
    }

    detail = (
        "Governed autonomous execution proof program complete"
        if success.get("program_complete")
        else "Governed autonomous execution proof composed — human review pending"
    )
    return GovernedAutonomousExecutionProofProgramResult(
        ok=True,
        session_id=sid,
        governed_autonomous_execution_proof_program=board,
        blockers=blockers,
        detail=detail,
    )
