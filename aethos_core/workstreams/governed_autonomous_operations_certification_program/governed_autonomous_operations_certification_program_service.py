# SPDX-License-Identifier: Apache-2.0
"""PHASE_I3 / FIX 363 — governed autonomous operations certification service."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.governance.governance_friction_approval_contract import FIX_363_CERTIFICATION_REQUIREMENTS
from aethos_core.workstreams.governed_autonomous_operations_certification_program.governed_autonomous_operations_certification_program_contract import (
    APPROVAL_BYPASS_FIX_363,
    AUTHORITY_EXPANSION_FIX_363,
    AUTONOMOUS_AUTHORITY_FIX_363,
    AUTONOMOUS_CERTIFICATION_CANDIDATE_MIN_SIZE,
    AUTONOMOUS_CERTIFICATION_SUSTAINED_MIN_SIZE,
    AUTONOMOUS_OPERATIONS_CERTIFICATION_LEVELS,
    AUTONOMOUS_OPERATIONS_CERTIFICATION_METRICS,
    CORE_PRINCIPLE,
    EXECUTIVE_WORKSTREAM_MODULES,
    FORBIDDEN_AUTONOMOUS_CERTIFICATION_ACTIONS,
    GOVERNANCE_BYPASS_AUTHORITY_FIX_363,
    GOVERNANCE_BYPASS_FIX_363,
    GOVERNANCE_MUTATION_FIX_363,
    GOVERNANCE_MUTATION_PERFORMED_FIX_363,
    GOVERNED_AUTONOMOUS_OPERATIONS_CERTIFICATION_PHASES,
    GOVERNED_AUTONOMOUS_OPERATIONS_CERTIFICATION_PROGRAM_FIX,
    GOVERNED_AUTONOMOUS_OPERATIONS_CERTIFICATION_PROGRAM_ID,
    GOVERNED_AUTONOMOUS_OPERATIONS_CERTIFICATION_PROGRAM_INVARIANT,
    GOVERNED_AUTONOMOUS_OPERATIONS_CERTIFICATION_PROGRAM_SCHEMA_VERSION,
    LOCAL_GOVERNED_AUTONOMOUS_OPERATIONS_CERTIFICATION_EXECUTABLE_FIX_363,
    MUTATION_PERFORMED_FIX_363,
    PROGRAM_NON_GOALS,
    TRUST_MUTATION_AUTHORITY_FIX_363,
    TRUST_PROMOTION_FIX_363,
)
from aethos_core.workstreams.governed_autonomous_operations_certification_program.governed_autonomous_operations_certification_program_executor import (
    build_autonomous_capability_certification_matrix,
    build_autonomous_certification_candidate_registry,
    build_autonomous_certification_opportunity_registry,
    build_autonomous_intervention_certification_report,
    build_autonomous_recovery_certification_report,
    build_autonomous_reliability_certification_report,
    build_multi_environment_certification_report,
    compute_autonomous_operations_certification_metrics,
)
from aethos_core.workstreams.governed_autonomous_operations_certification_program.governed_autonomous_operations_certification_program_store import (
    has_autonomous_certification_review_approve,
    list_autonomous_certification_records,
)


@dataclass(frozen=True)
class GovernedAutonomousOperationsCertificationProgramResult:
    ok: bool
    session_id: str
    governed_autonomous_operations_certification_program: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _session_records(records: list[dict[str, Any]], *, session_id: str) -> list[dict[str, Any]]:
    return [r for r in records if str(r.get("session_id") or session_id) == session_id]


def _build_phase_8_executive_visibility(*, program_session_id: str) -> dict[str, Any]:
    metrics = compute_autonomous_operations_certification_metrics(program_session_id=program_session_id)
    capabilities = build_autonomous_capability_certification_matrix(program_session_id=program_session_id)
    return {
        "autonomous_operations_certification_dashboard": {
            "dashboard_id": "autonomous-operations-certification-dashboard",
            "program_session_id": program_session_id,
            "execution_tracks": ["ET1", "ET2", "ET3", "ET4", "ET5"],
            "executive_workstream_modules": list(EXECUTIVE_WORKSTREAM_MODULES),
            "phase_i1_autonomous_execution_maturity_reference": {
                "phase": "PHASE_I1",
                "composed_read_only": True,
            },
            "phase_i2_autonomous_execution_proof_reference": {
                "phase": "PHASE_I2",
                "composed_read_only": True,
            },
            "workstream_d2_multi_cloud_proof_reference": {
                "workstream": "WORKSTREAM_D2",
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
            "autonomous_operations_certification_metrics": metrics,
            "autonomous_operations_certification_level": metrics.get("autonomous_operations_certification_level"),
            "certified_capability_count": len(capabilities.get("certified_capabilities") or []),
            "autonomous_authority_granted": False,
            "read_only": True,
        }
    }


def _build_phase_9_human_review(*, program_session_id: str) -> dict[str, Any]:
    records = _session_records(list_autonomous_certification_records(), session_id=program_session_id)
    notes = [r for r in records if str(r.get("kind") or "") == "autonomous_certification_note"]
    decisions = [r for r in records if str(r.get("kind") or "").startswith("autonomous_certification_review_")]
    return {
        "autonomous_operations_certification_review_registry": {
            "registry_id": "autonomous-operations-certification-review-registry",
            "note_count": len(notes),
            "decision_count": len(decisions),
            "notes": notes[-10:],
            "decisions": decisions[-5:],
            "read_only": True,
        }
    }


def _success_criteria(*, program_session_id: str) -> dict[str, Any]:
    registry = build_autonomous_certification_candidate_registry(program_session_id=program_session_id)
    reliability = build_autonomous_reliability_certification_report(program_session_id=program_session_id)
    recovery = build_autonomous_recovery_certification_report(program_session_id=program_session_id)
    intervention = build_autonomous_intervention_certification_report(program_session_id=program_session_id)
    metrics = compute_autonomous_operations_certification_metrics(program_session_id=program_session_id)

    return {
        "certification_candidate_registry_demonstrated": registry.get("candidate_count", 0) >= AUTONOMOUS_CERTIFICATION_CANDIDATE_MIN_SIZE,
        "sustained_execution_success_demonstrated": reliability.get("sustained_execution_success_demonstrated") is True,
        "sustained_deployment_success_demonstrated": reliability.get("sustained_deployment_success_demonstrated") is True,
        "sustained_verification_success_demonstrated": reliability.get("sustained_verification_success_demonstrated") is True,
        "sustained_recovery_success_demonstrated": recovery.get("sustained_recovery_success_demonstrated") is True,
        "declining_intervention_demonstrated": intervention.get("declining_intervention_demonstrated") is True,
        "governed_autonomous_operations_certification_signals": float(metrics.get("autonomous_operations_certification_score") or 0) >= 0.35,
        "autonomous_authority_granted": False,
        "approval_bypass_performed": False,
        "program_complete": has_autonomous_certification_review_approve(program_session_id=program_session_id),
    }


def build_governed_autonomous_operations_certification_program(
    *, session_id: str = "default"
) -> GovernedAutonomousOperationsCertificationProgramResult:
    sid = (session_id or "default").strip()[:64] or "default"
    blockers: list[str] = []

    sections: dict[str, list[dict[str, Any]]] = {
        "phase_1_certification_candidate_registry": [
            {
                "autonomous_certification_candidate_registry": build_autonomous_certification_candidate_registry(
                    program_session_id=sid
                )
            }
        ],
        "phase_2_reliability_certification_analysis": [
            {
                "autonomous_reliability_certification_report": build_autonomous_reliability_certification_report(
                    program_session_id=sid
                )
            }
        ],
        "phase_3_recovery_certification_analysis": [
            {
                "autonomous_recovery_certification_report": build_autonomous_recovery_certification_report(
                    program_session_id=sid
                )
            }
        ],
        "phase_4_human_intervention_certification_analysis": [
            {
                "autonomous_intervention_certification_report": build_autonomous_intervention_certification_report(
                    program_session_id=sid
                )
            }
        ],
        "phase_5_capability_certification_matrix": [
            {
                "autonomous_capability_certification_matrix": build_autonomous_capability_certification_matrix(
                    program_session_id=sid
                )
            }
        ],
        "phase_6_multi_environment_certification": [
            {"multi_environment_certification_report": build_multi_environment_certification_report(program_session_id=sid)}
        ],
        "phase_7_certification_opportunity_registry": [
            {
                "autonomous_certification_opportunity_registry": build_autonomous_certification_opportunity_registry(
                    program_session_id=sid
                )
            }
        ],
        "phase_8_executive_visibility": [_build_phase_8_executive_visibility(program_session_id=sid)],
        "phase_9_human_review": [_build_phase_9_human_review(program_session_id=sid)],
    }

    success = _success_criteria(program_session_id=sid)
    metrics = compute_autonomous_operations_certification_metrics(program_session_id=sid)
    candidate_count = build_autonomous_certification_candidate_registry(program_session_id=sid).get("candidate_count", 0)

    if candidate_count < AUTONOMOUS_CERTIFICATION_CANDIDATE_MIN_SIZE:
        blockers.append("autonomous_certification_candidate_minimum_not_met")
    if not has_autonomous_certification_review_approve(program_session_id=sid):
        blockers.append("autonomous_certification_review_approve_required")

    board: dict[str, Any] = {
        "schema_version": GOVERNED_AUTONOMOUS_OPERATIONS_CERTIFICATION_PROGRAM_SCHEMA_VERSION,
        "phase_id": GOVERNED_AUTONOMOUS_OPERATIONS_CERTIFICATION_PROGRAM_ID,
        "workstream_id": GOVERNED_AUTONOMOUS_OPERATIONS_CERTIFICATION_PROGRAM_ID,
        "fix_id": GOVERNED_AUTONOMOUS_OPERATIONS_CERTIFICATION_PROGRAM_FIX,
        "exported_at": _exported_at(),
        "session_id": sid,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_363,
        "core_principle": CORE_PRINCIPLE,
        "invariant": GOVERNED_AUTONOMOUS_OPERATIONS_CERTIFICATION_PROGRAM_INVARIANT,
        "forbidden_actions": [f"{key}: {value}" for key, value in FORBIDDEN_AUTONOMOUS_CERTIFICATION_ACTIONS],
        "non_goals": list(PROGRAM_NON_GOALS),
        "phases": list(GOVERNED_AUTONOMOUS_OPERATIONS_CERTIFICATION_PHASES),
        "autonomous_authority": AUTONOMOUS_AUTHORITY_FIX_363,
        "authority_expansion": AUTHORITY_EXPANSION_FIX_363,
        "governance_mutation": GOVERNANCE_MUTATION_FIX_363,
        "governance_bypass": GOVERNANCE_BYPASS_FIX_363,
        "trust_promotion": TRUST_PROMOTION_FIX_363,
        "approval_bypass": APPROVAL_BYPASS_FIX_363,
        "governance_bypass_authority": GOVERNANCE_BYPASS_AUTHORITY_FIX_363,
        "trust_mutation_authority": TRUST_MUTATION_AUTHORITY_FIX_363,
        "local_governed_autonomous_operations_certification_executable": LOCAL_GOVERNED_AUTONOMOUS_OPERATIONS_CERTIFICATION_EXECUTABLE_FIX_363,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_363,
        "autonomous_certification_candidate_minimum_size": AUTONOMOUS_CERTIFICATION_CANDIDATE_MIN_SIZE,
        "autonomous_certification_sustained_minimum_size": AUTONOMOUS_CERTIFICATION_SUSTAINED_MIN_SIZE,
        "autonomous_operations_certification_levels": list(AUTONOMOUS_OPERATIONS_CERTIFICATION_LEVELS),
        "metrics_tracked": list(AUTONOMOUS_OPERATIONS_CERTIFICATION_METRICS),
        "metrics": metrics,
        "success_criteria": success,
        "composed_from_phase_i1_i2_et1_et5_d2_g4_h3_patterns": True,
        "sections": sections,
        "fix_363_certification_requirements": list(FIX_363_CERTIFICATION_REQUIREMENTS),
    }

    detail = (
        "Governed autonomous operations certification program complete"
        if success.get("program_complete")
        else "Governed autonomous operations certification composed — human review pending"
    )
    return GovernedAutonomousOperationsCertificationProgramResult(
        ok=True,
        session_id=sid,
        governed_autonomous_operations_certification_program=board,
        blockers=blockers,
        detail=detail,
    )
