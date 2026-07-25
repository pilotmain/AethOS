# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_C1 / FIX 339 — compose real world delivery proof program."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.governance.governance_friction_approval_contract import FIX_339_CERTIFICATION_REQUIREMENTS
from aethos_core.workstreams.real_world_delivery_proof_program.real_world_delivery_proof_program_contract import (
    AUTHORITY_EXPANSION_FIX_339,
    AUTOMATIC_PRODUCTION_PROMOTION_FIX_339,
    CANDIDATE_TYPES,
    CORE_PRINCIPLE,
    DELIVERY_AUTHORITY_FIX_339,
    DELIVERY_PROOF_METRICS,
    EXECUTIVE_FIX_MODULES,
    FORBIDDEN_DELIVERY_PROOF_ACTIONS,
    GOVERNANCE_BYPASS_AUTHORITY_FIX_339,
    GOVERNANCE_MUTATION_PERFORMED_FIX_339,
    LOCAL_DELIVERY_PROOF_EXECUTABLE_FIX_339,
    MUTATION_PERFORMED_FIX_339,
    PROGRAM_NON_GOALS,
    REAL_WORLD_DELIVERY_PROOF_PHASES,
    REAL_WORLD_DELIVERY_PROOF_PROGRAM_FIX,
    REAL_WORLD_DELIVERY_PROOF_PROGRAM_ID,
    REAL_WORLD_DELIVERY_PROOF_PROGRAM_INVARIANT,
    REAL_WORLD_DELIVERY_PROOF_PROGRAM_SCHEMA_VERSION,
    REPOSITORY_LABELS,
    TRUST_MUTATION_AUTHORITY_FIX_339,
    WAVE_1_REPOSITORIES,
)
from aethos_core.workstreams.real_world_delivery_proof_program.real_world_delivery_proof_program_executor import (
    analyze_delivery_trust_impact,
    build_operational_proof_evidence_bundle,
    compute_delivery_proof_metrics,
)
from aethos_core.workstreams.real_world_delivery_proof_program.real_world_delivery_proof_program_store import (
    has_delivery_proof_review_approve,
    list_delivery_candidate_registry_entries,
    list_delivery_execution_registry_entries,
    list_delivery_incident_registry_entries,
    list_delivery_verification_registry_entries,
    list_real_world_delivery_proof_records,
)


@dataclass(frozen=True)
class RealWorldDeliveryProofProgramResult:
    ok: bool
    session_id: str
    real_world_delivery_proof_program: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _session_records(records: list[dict[str, Any]], *, session_id: str) -> list[dict[str, Any]]:
    return [r for r in records if str(r.get("session_id") or session_id) == session_id]


def _build_phase_1_candidate_selection(*, session_id: str) -> dict[str, Any]:
    candidates = [
        row for row in list_delivery_candidate_registry_entries() if str(row.get("session_id") or "") == session_id
    ]
    if not candidates:
        candidates = [
            {
                "candidate_id": f"candidate-{repo.replace('/', '-')}",
                "session_id": session_id,
                "repository": repo,
                "display_name": REPOSITORY_LABELS.get(repo, repo),
                "candidate_types": list(CANDIDATE_TYPES),
                "risk_profile": "low",
                "selection_status": "AVAILABLE",
                "read_only": True,
            }
            for repo in WAVE_1_REPOSITORIES
        ]

    delivery_candidate_registry = {
        "registry_id": "delivery-candidate-registry",
        "wave": 1,
        "candidate_count": len(candidates),
        "candidates": candidates[-20:],
        "candidate_types": list(CANDIDATE_TYPES),
        "repositories": [
            {"repository": repo, "display_name": REPOSITORY_LABELS.get(repo, repo)} for repo in WAVE_1_REPOSITORIES
        ],
        "read_only": True,
    }
    return {"delivery_candidate_registry": delivery_candidate_registry}


def _build_phase_2_delivery_execution(*, session_id: str) -> dict[str, Any]:
    executions = [
        row for row in list_delivery_execution_registry_entries() if str(row.get("session_id") or "") == session_id
    ]
    delivery_execution_registry = {
        "registry_id": "delivery-execution-registry",
        "execution_count": len(executions),
        "executions": executions[-10:],
        "execution_tracks": ["ET1", "ET2", "ET3", "ET4"],
        "read_only": True,
    }
    return {"delivery_execution_registry": delivery_execution_registry}


def _build_phase_3_verification(*, session_id: str) -> dict[str, Any]:
    verifications = [
        row for row in list_delivery_verification_registry_entries() if str(row.get("session_id") or "") == session_id
    ]
    delivery_verification_registry = {
        "registry_id": "delivery-verification-registry",
        "verification_count": len(verifications),
        "verifications": verifications[-10:],
        "checks": [
            "deployment_success",
            "endpoint_health",
            "artifact_integrity",
            "repository_integrity",
        ],
        "read_only": True,
    }
    return {"delivery_verification_registry": delivery_verification_registry}


def _build_phase_4_reliability_tracking(*, session_id: str) -> dict[str, Any]:
    metrics = compute_delivery_proof_metrics(session_id=session_id)
    executions = [
        row for row in list_delivery_execution_registry_entries() if str(row.get("session_id") or "") == session_id
    ]
    total = len(executions)
    passed = sum(1 for row in executions if row.get("passed") is True)
    failed = total - passed

    delivery_reliability_report = {
        "report_id": "delivery-reliability-report",
        "success_rate": round(passed / total, 4) if total else 0.0,
        "failure_rate": round(failed / total, 4) if total else 0.0,
        "intervention_rate": round(
            metrics.get("human_interventions", 0) / total, 4
        )
        if total
        else 0.0,
        "average_completion_time_ms": metrics.get("time_to_delivery_ms"),
        "metrics": metrics,
        "read_only": True,
    }
    return {"delivery_reliability_report": delivery_reliability_report}


def _build_phase_5_incident_tracking(*, session_id: str) -> dict[str, Any]:
    incidents = [
        row for row in list_delivery_incident_registry_entries() if str(row.get("session_id") or "") == session_id
    ]
    delivery_incident_registry = {
        "registry_id": "delivery-incident-registry",
        "incident_count": len(incidents),
        "incidents": incidents[-10:],
        "generation_failures": sum(1 for row in incidents if row.get("incident_class") == "generation_failure"),
        "git_failures": sum(1 for row in incidents if row.get("incident_class") == "git_failure"),
        "deployment_failures": sum(1 for row in incidents if row.get("incident_class") == "deployment_failure"),
        "verification_failures": sum(1 for row in incidents if row.get("incident_class") == "verification_failure"),
        "read_only": True,
    }
    return {"delivery_incident_registry": delivery_incident_registry}


def _build_phase_6_operational_evidence(*, session_id: str) -> dict[str, Any]:
    operational_proof_evidence_bundle = build_operational_proof_evidence_bundle(session_id=session_id)
    return {"operational_proof_evidence_bundle": operational_proof_evidence_bundle}


def _build_phase_7_executive_visibility(*, session_id: str) -> dict[str, Any]:
    metrics = compute_delivery_proof_metrics(session_id=session_id)
    evidence_representable = metrics.get("successful_deliveries", 0) > 0

    module_assessments: dict[str, Any] = {}
    for fix_label in EXECUTIVE_FIX_MODULES:
        if fix_label == "FIX 316":
            module_assessments[fix_label] = {
                "delivery_proof_representable": evidence_representable,
                "operations_incident_visibility": metrics.get("incident_count", 0) >= 0,
                "compose_available": True,
            }
        elif fix_label == "FIX 324":
            module_assessments[fix_label] = {
                "portfolio_delivery_signals_available": evidence_representable,
                "compose_available": True,
            }
        elif fix_label == "FIX 329":
            module_assessments[fix_label] = {
                "operating_review_evidence_available": evidence_representable,
                "compose_available": True,
            }
        elif fix_label == "FIX 330":
            module_assessments[fix_label] = {
                "executive_dashboard_evidence_gate": evidence_representable,
                "compose_available": True,
            }

    delivery_proof_dashboard = {
        "dashboard_id": "delivery-proof-dashboard",
        "wave_1_repositories": list(WAVE_1_REPOSITORIES),
        "successful_deliveries": metrics.get("successful_deliveries"),
        "failed_deliveries": metrics.get("failed_deliveries"),
        "deployments_verified": metrics.get("deployments_verified"),
        "module_assessments": module_assessments,
        "executive_fix_modules": list(EXECUTIVE_FIX_MODULES),
        "read_only": True,
    }
    return {"delivery_proof_dashboard": delivery_proof_dashboard}


def _build_phase_8_trust_impact_analysis(*, session_id: str) -> dict[str, Any]:
    delivery_trust_impact_report = analyze_delivery_trust_impact(session_id=session_id)
    return {"delivery_trust_impact_report": delivery_trust_impact_report}


def _build_phase_9_human_review(*, session_id: str) -> dict[str, Any]:
    records = _session_records(list_real_world_delivery_proof_records(), session_id=session_id)
    notes = [r for r in records if str(r.get("kind") or "") == "delivery_proof_note"]
    decisions = [r for r in records if str(r.get("kind") or "").startswith("delivery_proof_review_")]

    delivery_proof_review_registry = {
        "registry_id": "delivery-proof-review-registry",
        "note_count": len(notes),
        "decision_count": len(decisions),
        "notes": notes[-10:],
        "decisions": decisions[-5:],
        "human_review_required": True,
        "read_only": True,
    }
    return {"delivery_proof_review_registry": delivery_proof_review_registry}


def _success_criteria(*, session_id: str) -> dict[str, Any]:
    metrics = compute_delivery_proof_metrics(session_id=session_id)
    trust = analyze_delivery_trust_impact(session_id=session_id)
    return {
        "successful_deliveries": metrics.get("successful_deliveries", 0) > 0,
        "repeatable_deliveries": metrics.get("successful_deliveries", 0) >= 2,
        "measurable_delivery_quality": metrics.get("time_to_delivery_ms", 0) >= 0,
        "operational_stability": trust.get("execution_maturity") in {"EMERGING", "REPEATABLE"},
        "human_proof_review_approved": has_delivery_proof_review_approve(session_id=session_id),
        "program_complete": (
            metrics.get("successful_deliveries", 0) >= 1
            and has_delivery_proof_review_approve(session_id=session_id)
            and trust.get("trust_promotion_performed") is False
        ),
    }


def build_real_world_delivery_proof_program(*, session_id: str = "default") -> RealWorldDeliveryProofProgramResult:
    sid = (session_id or "default").strip()[:64] or "default"
    blockers: list[str] = []

    sections: dict[str, list[dict[str, Any]]] = {}
    phase_builders = (
        _build_phase_1_candidate_selection,
        _build_phase_2_delivery_execution,
        _build_phase_3_verification,
        _build_phase_4_reliability_tracking,
        _build_phase_5_incident_tracking,
        _build_phase_6_operational_evidence,
        _build_phase_7_executive_visibility,
        _build_phase_8_trust_impact_analysis,
        _build_phase_9_human_review,
    )
    for phase, builder in zip(REAL_WORLD_DELIVERY_PROOF_PHASES, phase_builders, strict=True):
        sections[phase] = [builder(session_id=sid)]

    success = _success_criteria(session_id=sid)
    metrics = compute_delivery_proof_metrics(session_id=sid)

    if metrics.get("successful_deliveries", 0) == 0:
        blockers.append("delivery_proof_executions_pending")
    if not has_delivery_proof_review_approve(session_id=sid):
        blockers.append("delivery_proof_review_approve_required")

    board: dict[str, Any] = {
        "schema_version": REAL_WORLD_DELIVERY_PROOF_PROGRAM_SCHEMA_VERSION,
        "workstream_id": REAL_WORLD_DELIVERY_PROOF_PROGRAM_ID,
        "fix_id": REAL_WORLD_DELIVERY_PROOF_PROGRAM_FIX,
        "exported_at": _exported_at(),
        "session_id": sid,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_339,
        "execution_performed": metrics.get("successful_deliveries", 0) > 0,
        "core_principle": CORE_PRINCIPLE,
        "invariant": REAL_WORLD_DELIVERY_PROOF_PROGRAM_INVARIANT,
        "forbidden_actions": [f"{key}: {value}" for key, value in FORBIDDEN_DELIVERY_PROOF_ACTIONS],
        "non_goals": list(PROGRAM_NON_GOALS),
        "phases": list(REAL_WORLD_DELIVERY_PROOF_PHASES),
        "wave_1_repositories": [
            {"repository": repo, "display_name": REPOSITORY_LABELS.get(repo, repo)} for repo in WAVE_1_REPOSITORIES
        ],
        "delivery_authority": DELIVERY_AUTHORITY_FIX_339,
        "trust_mutation_authority": TRUST_MUTATION_AUTHORITY_FIX_339,
        "authority_expansion": AUTHORITY_EXPANSION_FIX_339,
        "automatic_production_promotion": AUTOMATIC_PRODUCTION_PROMOTION_FIX_339,
        "governance_bypass_authority": GOVERNANCE_BYPASS_AUTHORITY_FIX_339,
        "local_delivery_proof_executable": LOCAL_DELIVERY_PROOF_EXECUTABLE_FIX_339,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_339,
        "metrics_tracked": list(DELIVERY_PROOF_METRICS),
        "metrics": metrics,
        "success_criteria": success,
        "composed_from_execution_tracks_1_through_5": True,
        "sections": sections,
        "sources": {
            "execution_track_1_workspace": True,
            "execution_track_2_changeset": True,
            "execution_track_3_git_delivery": True,
            "execution_track_4_deployment": True,
            "execution_track_5_certification": True,
            "fix_316_operations": True,
            "fix_324_portfolio": True,
            "fix_329_operating_review": True,
            "fix_330_executive_dashboard": True,
        },
        "fix_339_certification_requirements": list(FIX_339_CERTIFICATION_REQUIREMENTS),
    }

    detail = (
        "Real-world delivery proof program complete"
        if success.get("program_complete")
        else "Real-world delivery proof program composed — executions and human review pending"
    )
    return RealWorldDeliveryProofProgramResult(
        ok=True,
        session_id=sid,
        real_world_delivery_proof_program=board,
        blockers=blockers,
        detail=detail,
    )
