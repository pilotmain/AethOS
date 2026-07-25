# SPDX-License-Identifier: Apache-2.0
"""FIX 337 / EXECUTION_TRACK_4 — compose governed deployment execution track."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.execution_tracks.governed_deployment_execution.governed_deployment_execution_contract import (
    AUTONOMOUS_DEPLOYMENT_ENABLED_FIX_337,
    CORE_PRINCIPLE,
    DEPLOYMENT_AUTHORITY_FIX_337,
    EXECUTION_PERFORMED_FIX_337,
    EXECUTION_TRACK_4_ID,
    EXECUTION_TRACK_4_PHASES,
    FORBIDDEN_DEPLOYMENT_EXECUTION_ACTIONS,
    GOVERNED_DEPLOYMENT_EXECUTION_FIX,
    GOVERNED_DEPLOYMENT_EXECUTION_INVARIANT,
    GOVERNED_DEPLOYMENT_EXECUTION_PRINCIPLES,
    GOVERNED_DEPLOYMENT_EXECUTION_SCHEMA_VERSION,
    GOVERNANCE_MUTATION_PERFORMED_FIX_337,
    LOCAL_DEPLOYMENT_EXECUTION_EXECUTABLE_FIX_337,
    MUTATION_PERFORMED_FIX_337,
    PHASE_1_PROVIDERS,
    PHASE_2_PROVIDERS,
    PRODUCTION_PROMOTION_AUTHORITY_FIX_337,
    REQUIRED_DEPLOYMENT_REVIEW_KINDS,
    ROLLBACK_AUTHORITY_FIX_337,
    SUPPORTED_ENVIRONMENTS,
    TRACK_NON_GOALS,
    TRUST_MUTATION_AUTHORITY_FIX_337,
)
from aethos_core.execution_tracks.governed_deployment_execution.governed_deployment_execution_executor import (
    assess_deployment_failure,
    verify_deployment,
)
from aethos_core.execution_tracks.governed_deployment_execution.governed_deployment_execution_store import (
    all_deployment_reviews_recorded,
    has_deployment_decision_approve,
    has_deployment_executed,
    latest_record_by_kind,
    list_deployment_receipt_registry_entries,
    list_governed_deployment_execution_records,
)
from aethos_core.execution_tracks.governed_git_delivery.governed_git_delivery_store import (
    list_delivery_registry_entries,
)
from aethos_core.governance.governance_friction_approval_contract import FIX_337_CERTIFICATION_REQUIREMENTS


@dataclass(frozen=True)
class GovernedDeploymentExecutionResult:
    ok: bool
    session_id: str
    governed_deployment_execution: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _session_records(records: list[dict[str, Any]], *, session_id: str) -> list[dict[str, Any]]:
    return [r for r in records if str(r.get("session_id") or session_id) == session_id]


def _intake_metadata(*, session_id: str) -> dict[str, Any]:
    record = latest_record_by_kind(session_id=session_id, kind="deployment_review_note")
    return dict((record or {}).get("metadata") or {})


def _build_phase_1_deployment_request_intake(*, session_id: str) -> dict[str, Any]:
    records = _session_records(list_governed_deployment_execution_records(), session_id=session_id)
    requests = [r for r in records if str(r.get("kind") or "") == "deployment_review_note"]
    deliveries = [
        row for row in list_delivery_registry_entries() if str(row.get("session_id") or "") == session_id
    ]
    meta = _intake_metadata(session_id=session_id)

    deployment_request_registry = {
        "registry_id": "deployment-request-registry",
        "request_count": len(requests),
        "requests": requests[-10:],
        "approved_delivery_present": bool(deliveries),
        "read_only": True,
    }

    delivery = deliveries[-1] if deliveries else {}
    pr = delivery.get("pull_request_receipt") or {}
    deployment_scope_report = {
        "report_id": "deployment-scope-report",
        "provider": meta.get("provider"),
        "environment": meta.get("environment") or meta.get("env"),
        "delivery_id": delivery.get("delivery_id"),
        "pull_request_url": pr.get("pull_request_url"),
        "rollback_performed": False,
        "read_only": True,
    }

    return {
        "deployment_request_registry": deployment_request_registry,
        "deployment_scope_report": deployment_scope_report,
    }


def _build_phase_2_deployment_planning(*, session_id: str) -> dict[str, Any]:
    meta = _intake_metadata(session_id=session_id)
    provider = meta.get("provider") or "Railway"
    environment = meta.get("environment") or meta.get("env") or "staging"

    deployment_plan_report = {
        "report_id": "deployment-plan-report",
        "provider": provider,
        "environment": environment,
        "deployment_target": meta.get("target") or meta.get("service") or meta.get("project"),
        "verification_requirements": ["endpoint_reachable", "health_check_passed", "evidence_captured"],
        "phase_1_providers": list(PHASE_1_PROVIDERS),
        "phase_2_providers": list(PHASE_2_PROVIDERS),
        "read_only": True,
    }

    receipts = [
        row for row in list_deployment_receipt_registry_entries() if str(row.get("session_id") or "") == session_id
    ]
    deployment_target_registry = {
        "registry_id": "deployment-target-registry",
        "entry_count": len(receipts),
        "targets": [
            {
                "deployment_id": row.get("deployment_id"),
                "provider": row.get("provider"),
                "environment": row.get("environment"),
                "deployment_url": row.get("deployment_url"),
            }
            for row in receipts[-5:]
        ],
        "supported_environments": list(SUPPORTED_ENVIRONMENTS),
        "read_only": True,
    }

    return {
        "deployment_plan_report": deployment_plan_report,
        "deployment_target_registry": deployment_target_registry,
    }


def _build_phase_3_deployment_readiness(*, session_id: str) -> dict[str, Any]:
    meta = _intake_metadata(session_id=session_id)
    provider = str(meta.get("provider") or "Railway")
    readiness_review = latest_record_by_kind(session_id=session_id, kind="deployment_readiness_review_note")

    deployment_readiness_report = {
        "report_id": "deployment-readiness-report",
        "provider_configured": provider in PHASE_1_PROVIDERS or provider in PHASE_2_PROVIDERS,
        "permissions_valid": bool(readiness_review),
        "deployment_path_valid": bool(meta.get("provider")),
        "environment_healthy": str(meta.get("environment") or "staging") in SUPPORTED_ENVIRONMENTS,
        "readiness_review_recorded": bool(readiness_review),
        "ready_for_execution_review": all_deployment_reviews_recorded(session_id=session_id),
        "read_only": True,
    }
    return {"deployment_readiness_report": deployment_readiness_report}


def _build_phase_4_deployment_execution(*, session_id: str) -> dict[str, Any]:
    receipts = [
        row for row in list_deployment_receipt_registry_entries() if str(row.get("session_id") or "") == session_id
    ]
    latest = receipts[-1] if receipts else {}

    deployment_execution_report = {
        "report_id": "deployment-execution-report",
        "deployment_executed": has_deployment_executed(session_id=session_id),
        "provider": latest.get("provider"),
        "environment": latest.get("environment"),
        "deployment_url": latest.get("deployment_url"),
        "status": (latest.get("execution_receipt") or {}).get("status"),
        "rollback_performed": False,
        "read_only": True,
    }

    deployment_receipt_registry = {
        "registry_id": "deployment-receipt-registry",
        "entry_count": len(receipts),
        "entries": receipts[-5:],
        "read_only": True,
    }

    return {
        "deployment_execution_report": deployment_execution_report,
        "deployment_receipt_registry": deployment_receipt_registry,
    }


def _build_phase_5_post_deploy_verification(*, session_id: str) -> dict[str, Any]:
    verification = verify_deployment(session_id=session_id)
    deployment_verification_report = {
        "report_id": "deployment-verification-report",
        **verification,
        "read_only": True,
    }
    return {"deployment_verification_report": deployment_verification_report}


def _build_phase_6_operational_evidence(*, session_id: str) -> dict[str, Any]:
    receipts = [
        row for row in list_deployment_receipt_registry_entries() if str(row.get("session_id") or "") == session_id
    ]
    latest = receipts[-1] if receipts else {}
    verification = verify_deployment(session_id=session_id)

    deployment_evidence_bundle = {
        "bundle_id": "deployment-evidence-bundle",
        "execution_receipt": latest.get("execution_receipt"),
        "verification_receipt": latest.get("verification_receipt"),
        "verification_summary": verification,
        "timestamps": {
            "registered_at": latest.get("registered_at"),
            "verified_at": (latest.get("verification_receipt") or {}).get("verified_at"),
        },
        "provider_metadata": {
            "provider": latest.get("provider"),
            "environment": latest.get("environment"),
            "deployment_url": latest.get("deployment_url"),
        },
        "evidence_complete": verification.get("verified") is True,
        "read_only": True,
    }
    return {"deployment_evidence_bundle": deployment_evidence_bundle}


def _build_phase_7_failure_assessment(*, session_id: str) -> dict[str, Any]:
    deployment_failure_assessment = assess_deployment_failure(session_id=session_id)
    return {"deployment_failure_assessment": deployment_failure_assessment}


def _build_phase_8_deployment_dashboard(*, session_id: str) -> dict[str, Any]:
    verification = verify_deployment(session_id=session_id)
    failure = assess_deployment_failure(session_id=session_id)
    receipts = [
        row for row in list_deployment_receipt_registry_entries() if str(row.get("session_id") or "") == session_id
    ]
    latest = receipts[-1] if receipts else {}

    deployment_execution_dashboard = {
        "dashboard_id": "deployment-execution-dashboard",
        "deployment_status": "EXECUTED" if has_deployment_executed(session_id=session_id) else "PENDING",
        "verification_status": "VERIFIED" if verification.get("verified") else "PENDING",
        "failure_status": "NONE" if not failure.get("failure_detected") else failure.get("failure_class"),
        "provider": latest.get("provider"),
        "environment": latest.get("environment"),
        "deployment_reviews_complete": all_deployment_reviews_recorded(session_id=session_id),
        "deployment_decision_approve": has_deployment_decision_approve(session_id=session_id),
        "review_status": latest.get("review_status", "PENDING"),
        "handoff_ready": verification.get("verified") is True,
        "rollback_authority": False,
        "read_only": True,
    }
    return {"deployment_execution_dashboard": deployment_execution_dashboard}


def _build_phase_9_human_review(*, session_id: str) -> dict[str, Any]:
    records = _session_records(list_governed_deployment_execution_records(), session_id=session_id)
    decisions = [r for r in records if str(r.get("kind") or "").startswith("deployment_decision_")]
    reviews = [r for r in records if str(r.get("kind") or "").endswith("_review_note")]

    deployment_review_registry = {
        "registry_id": "deployment-review-registry",
        "review_count": len(reviews),
        "decision_count": len(decisions),
        "required_review_kinds": list(REQUIRED_DEPLOYMENT_REVIEW_KINDS),
        "reviews": reviews[-10:],
        "decisions": decisions[-5:],
        "read_only": True,
    }
    return {"deployment_review_registry": deployment_review_registry}


def _success_criteria(*, session_id: str) -> dict[str, Any]:
    verification = verify_deployment(session_id=session_id)
    approved = has_deployment_decision_approve(session_id=session_id)
    executed = has_deployment_executed(session_id=session_id)
    return {
        "deployment_prepared": all_deployment_reviews_recorded(session_id=session_id),
        "deployment_executed": executed,
        "deployment_receipts_collected": executed,
        "verification_performed": verification.get("verified") is True,
        "results_reported": executed,
        "governance_controls_respected": True,
        "track_complete": approved and executed and verification.get("verified") is True,
    }


def build_governed_deployment_execution(*, session_id: str = "default") -> GovernedDeploymentExecutionResult:
    sid = (session_id or "default").strip()[:64] or "default"
    blockers: list[str] = []

    sections: dict[str, list[dict[str, Any]]] = {}
    phase_builders = (
        _build_phase_1_deployment_request_intake,
        _build_phase_2_deployment_planning,
        _build_phase_3_deployment_readiness,
        _build_phase_4_deployment_execution,
        _build_phase_5_post_deploy_verification,
        _build_phase_6_operational_evidence,
        _build_phase_7_failure_assessment,
        _build_phase_8_deployment_dashboard,
        _build_phase_9_human_review,
    )
    for phase, builder in zip(EXECUTION_TRACK_4_PHASES, phase_builders, strict=True):
        sections[phase] = [builder(session_id=sid)]

    success = _success_criteria(session_id=sid)
    if not all_deployment_reviews_recorded(session_id=sid):
        blockers.append("deployment_review_gates_incomplete")
    if not has_deployment_decision_approve(session_id=sid):
        blockers.append("deployment_decision_approve_required")
    if not has_deployment_executed(session_id=sid):
        blockers.append("deployment_execution_pending")

    board: dict[str, Any] = {
        "schema_version": GOVERNED_DEPLOYMENT_EXECUTION_SCHEMA_VERSION,
        "execution_track_id": EXECUTION_TRACK_4_ID,
        "fix_id": GOVERNED_DEPLOYMENT_EXECUTION_FIX,
        "exported_at": _exported_at(),
        "session_id": sid,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_337,
        "execution_performed": has_deployment_executed(session_id=sid),
        "core_principle": CORE_PRINCIPLE,
        "invariant": GOVERNED_DEPLOYMENT_EXECUTION_INVARIANT,
        "principles": [f"{key}: {value}" for key, value in GOVERNED_DEPLOYMENT_EXECUTION_PRINCIPLES],
        "forbidden_actions": [f"{key}: {value}" for key, value in FORBIDDEN_DEPLOYMENT_EXECUTION_ACTIONS],
        "non_goals": list(TRACK_NON_GOALS),
        "phases": list(EXECUTION_TRACK_4_PHASES),
        "deployment_authority": DEPLOYMENT_AUTHORITY_FIX_337,
        "autonomous_deployment_enabled": AUTONOMOUS_DEPLOYMENT_ENABLED_FIX_337,
        "rollback_authority": ROLLBACK_AUTHORITY_FIX_337,
        "trust_mutation_authority": TRUST_MUTATION_AUTHORITY_FIX_337,
        "production_promotion_authority": PRODUCTION_PROMOTION_AUTHORITY_FIX_337,
        "local_deployment_execution_executable": LOCAL_DEPLOYMENT_EXECUTION_EXECUTABLE_FIX_337,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_337,
        "execution_performed_default": EXECUTION_PERFORMED_FIX_337,
        "success_criteria": success,
        "composed_from_execution_track_3": True,
        "sections": sections,
        "sources": {
            "execution_track_1_workspace": True,
            "execution_track_2_changeset": True,
            "execution_track_3_git_delivery": True,
        },
        "fix_337_certification_requirements": list(FIX_337_CERTIFICATION_REQUIREMENTS),
    }

    detail = (
        "Governed deployment execution track complete"
        if success.get("track_complete")
        else "Governed deployment execution track composed — deployment pending human approval"
    )
    return GovernedDeploymentExecutionResult(
        ok=True,
        session_id=sid,
        governed_deployment_execution=board,
        blockers=blockers,
        detail=detail,
    )
