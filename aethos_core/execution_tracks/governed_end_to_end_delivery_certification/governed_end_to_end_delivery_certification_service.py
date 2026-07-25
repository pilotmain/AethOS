# SPDX-License-Identifier: Apache-2.0
"""FIX 338 / EXECUTION_TRACK_5 — compose end-to-end delivery certification track."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.execution_tracks.governed_end_to_end_delivery_certification.governed_end_to_end_delivery_certification_contract import (
    APPROVAL_BYPASS_AUTHORITY_FIX_338,
    AUTHORITY_ESCALATION_FIX_338,
    AUTOMATIC_CERTIFICATION_PROMOTION_FIX_338,
    CERTIFICATION_SCENARIO_IDS,
    CERTIFICATION_SCENARIOS,
    CORE_PRINCIPLE,
    DELIVERY_AUTHORITY_FIX_338,
    DEPLOYMENT_BYPASS_AUTHORITY_FIX_338,
    EXECUTION_PERFORMED_FIX_338,
    EXECUTION_TRACK_5_ID,
    EXECUTION_TRACK_5_PHASES,
    FORBIDDEN_CERTIFICATION_ACTIONS,
    GOVERNED_END_TO_END_DELIVERY_CERTIFICATION_FIX,
    GOVERNED_END_TO_END_DELIVERY_CERTIFICATION_INVARIANT,
    GOVERNED_END_TO_END_DELIVERY_CERTIFICATION_PRINCIPLES,
    GOVERNED_END_TO_END_DELIVERY_CERTIFICATION_SCHEMA_VERSION,
    GOVERNANCE_MUTATION_PERFORMED_FIX_338,
    LOCAL_CERTIFICATION_EXECUTABLE_FIX_338,
    MUTATION_PERFORMED_FIX_338,
    REQUIRED_CERTIFICATION_REVIEW_KINDS,
    TRACK_NON_GOALS,
    TRUST_MUTATION_AUTHORITY_FIX_338,
)
from aethos_core.execution_tracks.governed_end_to_end_delivery_certification.governed_end_to_end_delivery_certification_executor import (
    analyze_delivery_failures,
    analyze_delivery_reliability,
    analyze_human_interventions,
    assess_certification_status,
    build_certification_evidence_bundle,
    measure_execution_quality,
)
from aethos_core.execution_tracks.governed_end_to_end_delivery_certification.governed_end_to_end_delivery_certification_store import (
    all_certification_reviews_recorded,
    has_certification_decision_approve,
    list_delivery_run_registry_entries,
    list_governed_end_to_end_delivery_certification_records,
)
from aethos_core.governance.governance_friction_approval_contract import FIX_338_CERTIFICATION_REQUIREMENTS


@dataclass(frozen=True)
class GovernedEndToEndDeliveryCertificationResult:
    ok: bool
    session_id: str
    governed_end_to_end_delivery_certification: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _session_records(records: list[dict[str, Any]], *, session_id: str) -> list[dict[str, Any]]:
    return [r for r in records if str(r.get("session_id") or session_id) == session_id]


def _build_phase_1_delivery_run_registry(*, session_id: str) -> dict[str, Any]:
    runs = [
        row for row in list_delivery_run_registry_entries() if str(row.get("session_id") or "") == session_id
    ]
    delivery_run_registry = {
        "registry_id": "delivery-run-registry",
        "run_count": len(runs),
        "runs": runs[-10:],
        "scenario_ids": list(CERTIFICATION_SCENARIO_IDS),
        "read_only": True,
    }
    return {"delivery_run_registry": delivery_run_registry}


def _build_phase_2_execution_quality(*, session_id: str) -> dict[str, Any]:
    execution_quality_report = measure_execution_quality(session_id=session_id)
    return {"execution_quality_report": execution_quality_report}


def _build_phase_3_reliability_analysis(*, session_id: str) -> dict[str, Any]:
    delivery_reliability_report = analyze_delivery_reliability(session_id=session_id)
    return {"delivery_reliability_report": delivery_reliability_report}


def _build_phase_4_failure_intelligence(*, session_id: str) -> dict[str, Any]:
    delivery_failure_analysis = analyze_delivery_failures(session_id=session_id)
    return {"delivery_failure_analysis": delivery_failure_analysis}


def _build_phase_5_human_intervention_analysis(*, session_id: str) -> dict[str, Any]:
    intervention_analysis_report = analyze_human_interventions(session_id=session_id)
    return {"intervention_analysis_report": intervention_analysis_report}


def _build_phase_6_evidence_certification(*, session_id: str) -> dict[str, Any]:
    delivery_certification_evidence_bundle = build_certification_evidence_bundle(session_id=session_id)
    return {"delivery_certification_evidence_bundle": delivery_certification_evidence_bundle}


def _build_phase_7_readiness_assessment(*, session_id: str) -> dict[str, Any]:
    delivery_certification_status = assess_certification_status(session_id=session_id)
    return {"delivery_certification_status": delivery_certification_status}


def _build_phase_8_certification_dashboard(*, session_id: str) -> dict[str, Any]:
    status = assess_certification_status(session_id=session_id)
    reliability = analyze_delivery_reliability(session_id=session_id)
    quality = measure_execution_quality(session_id=session_id)
    failures = analyze_delivery_failures(session_id=session_id)

    delivery_certification_dashboard = {
        "dashboard_id": "delivery-certification-dashboard",
        "certification_status": status.get("status"),
        "run_count": status.get("run_count"),
        "pass_rate": reliability.get("pass_rate"),
        "failure_rate": reliability.get("failure_rate"),
        "verification_success_rate": quality.get("verification_success_rate"),
        "failure_detected": failures.get("failure_detected"),
        "core_scenarios_passed": status.get("core_scenarios_passed"),
        "human_certification_approved": status.get("human_certification_approved"),
        "certification_reviews_complete": all_certification_reviews_recorded(session_id=session_id),
        "delivery_authority_granted": False,
        "read_only": True,
    }
    return {"delivery_certification_dashboard": delivery_certification_dashboard}


def _build_phase_9_human_review(*, session_id: str) -> dict[str, Any]:
    records = _session_records(list_governed_end_to_end_delivery_certification_records(), session_id=session_id)
    decisions = [r for r in records if str(r.get("kind") or "").startswith("certification_decision_")]
    reviews = [r for r in records if str(r.get("kind") or "").endswith("_review_note")]

    delivery_certification_review_registry = {
        "registry_id": "delivery-certification-review-registry",
        "review_count": len(reviews),
        "decision_count": len(decisions),
        "required_review_kinds": list(REQUIRED_CERTIFICATION_REVIEW_KINDS),
        "reviews": reviews[-10:],
        "decisions": decisions[-5:],
        "read_only": True,
    }
    return {"delivery_certification_review_registry": delivery_certification_review_registry}


def _success_criteria(*, session_id: str) -> dict[str, Any]:
    status = assess_certification_status(session_id=session_id)
    quality = measure_execution_quality(session_id=session_id)
    return {
        "end_to_end_delivery_demonstrated": status.get("run_count", 0) > 0,
        "repeatable_delivery": status.get("passed_count", 0) > 0,
        "evidence_backed_delivery": status.get("evidence_complete") is True,
        "measurable_delivery_quality": quality.get("run_count", 0) > 0,
        "certification_status": status.get("status"),
        "track_complete": status.get("status") in {"CERTIFIED", "PRODUCTION_CERTIFIED"},
    }


def build_governed_end_to_end_delivery_certification(
    *, session_id: str = "default"
) -> GovernedEndToEndDeliveryCertificationResult:
    sid = (session_id or "default").strip()[:64] or "default"
    blockers: list[str] = []

    sections: dict[str, list[dict[str, Any]]] = {}
    phase_builders = (
        _build_phase_1_delivery_run_registry,
        _build_phase_2_execution_quality,
        _build_phase_3_reliability_analysis,
        _build_phase_4_failure_intelligence,
        _build_phase_5_human_intervention_analysis,
        _build_phase_6_evidence_certification,
        _build_phase_7_readiness_assessment,
        _build_phase_8_certification_dashboard,
        _build_phase_9_human_review,
    )
    for phase, builder in zip(EXECUTION_TRACK_5_PHASES, phase_builders, strict=True):
        sections[phase] = [builder(session_id=sid)]

    success = _success_criteria(session_id=sid)
    status = assess_certification_status(session_id=sid)

    if not all_certification_reviews_recorded(session_id=sid):
        blockers.append("certification_review_gates_incomplete")
    if status.get("run_count", 0) == 0:
        blockers.append("certification_runs_pending")
    if not has_certification_decision_approve(session_id=sid):
        blockers.append("certification_decision_approve_required")

    board: dict[str, Any] = {
        "schema_version": GOVERNED_END_TO_END_DELIVERY_CERTIFICATION_SCHEMA_VERSION,
        "execution_track_id": EXECUTION_TRACK_5_ID,
        "fix_id": GOVERNED_END_TO_END_DELIVERY_CERTIFICATION_FIX,
        "exported_at": _exported_at(),
        "session_id": sid,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_338,
        "execution_performed": status.get("run_count", 0) > 0,
        "core_principle": CORE_PRINCIPLE,
        "invariant": GOVERNED_END_TO_END_DELIVERY_CERTIFICATION_INVARIANT,
        "principles": [f"{key}: {value}" for key, value in GOVERNED_END_TO_END_DELIVERY_CERTIFICATION_PRINCIPLES],
        "forbidden_actions": [f"{key}: {value}" for key, value in FORBIDDEN_CERTIFICATION_ACTIONS],
        "non_goals": list(TRACK_NON_GOALS),
        "phases": list(EXECUTION_TRACK_5_PHASES),
        "certification_scenarios": {
            scenario_id: scenario["name"] for scenario_id, scenario in CERTIFICATION_SCENARIOS.items()
        },
        "delivery_authority": DELIVERY_AUTHORITY_FIX_338,
        "trust_mutation_authority": TRUST_MUTATION_AUTHORITY_FIX_338,
        "automatic_certification_promotion": AUTOMATIC_CERTIFICATION_PROMOTION_FIX_338,
        "approval_bypass_authority": APPROVAL_BYPASS_AUTHORITY_FIX_338,
        "deployment_bypass_authority": DEPLOYMENT_BYPASS_AUTHORITY_FIX_338,
        "authority_escalation": AUTHORITY_ESCALATION_FIX_338,
        "local_certification_executable": LOCAL_CERTIFICATION_EXECUTABLE_FIX_338,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_338,
        "execution_performed_default": EXECUTION_PERFORMED_FIX_338,
        "success_criteria": success,
        "composed_from_execution_tracks_1_through_4": True,
        "sections": sections,
        "sources": {
            "execution_track_1_workspace": True,
            "execution_track_2_changeset": True,
            "execution_track_3_git_delivery": True,
            "execution_track_4_deployment": True,
        },
        "fix_338_certification_requirements": list(FIX_338_CERTIFICATION_REQUIREMENTS),
    }

    detail = (
        "End-to-end delivery certification complete"
        if success.get("track_complete")
        else "End-to-end delivery certification composed — runs and human review pending"
    )
    return GovernedEndToEndDeliveryCertificationResult(
        ok=True,
        session_id=sid,
        governed_end_to_end_delivery_certification=board,
        blockers=blockers,
        detail=detail,
    )
