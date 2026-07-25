# SPDX-License-Identifier: Apache-2.0
"""FIX 189 — bounded agent execution package runners (work within envelope)."""

from __future__ import annotations

from typing import Any, Callable

from aethos_core.mission_control.bounded_multi_agent_delivery_execution.bounded_multi_agent_delivery_execution_contract import (
    AGENT_EXECUTION_AUTHORITY_FIX_189,
    AGENT_EXECUTION_ROLE_IDS,
    DEPLOY_AUTHORITY_FIX_189,
    MERGE_AUTHORITY_FIX_189,
    PROVIDER_AUTHORITY_FIX_189,
    RAILWAY_AUTHORITY_FIX_189,
)
from aethos_core.software_delivery.issue_intake_scope_fidelity_service import assess_plan_scope_fidelity
from aethos_core.software_delivery.issue_plan_store import load_issue_plan_for_session
from aethos_core.software_delivery.patch_proposal_store import load_patch_proposal_for_plan

ExecutionRunner = Callable[..., dict[str, Any]]


def _authority_flags() -> dict[str, bool]:
    return {
        "agent_execution_authority": AGENT_EXECUTION_AUTHORITY_FIX_189,
        "merge_authority": MERGE_AUTHORITY_FIX_189,
        "deploy_authority": DEPLOY_AUTHORITY_FIX_189,
        "railway_authority": RAILWAY_AUTHORITY_FIX_189,
        "provider_authority": PROVIDER_AUTHORITY_FIX_189,
        "gate_bypass": False,
    }


def _blocked(
    *,
    role_id: str,
    title: str,
    blockers: list[str],
    detail: str = "",
) -> dict[str, Any]:
    return {
        "agent_role_id": role_id,
        "title": title,
        "status": "blocked",
        "work_performed": False,
        "blockers": blockers,
        "detail": detail,
        **_authority_flags(),
    }


def execute_planner_agent_package(*, session_id: str, plan_id: str | None) -> dict[str, Any]:
    from aethos_core.software_delivery.issue_plan_service import create_implementation_plan

    plan = load_issue_plan_for_session(session_id=session_id)
    if not plan:
        return _blocked(
            role_id="planner_agent",
            title="PlannerAgent — implementation plan generation",
            blockers=["issue_plan_missing"],
            detail="Analyze GitHub issue before planner execution package.",
        )

    result = create_implementation_plan(session_id=session_id)
    plan = result.plan or plan
    governed = dict(plan.get("governed_plan") or {})
    tasks = list(governed.get("tasks") or governed.get("steps") or [])
    dependencies = list(governed.get("dependencies") or [])

    return {
        "agent_role_id": "planner_agent",
        "title": "PlannerAgent — implementation plan generation",
        "status": "completed" if result.ok else "partial",
        "work_performed": result.ok,
        "artifact_type": "governed_implementation_plan",
        "plan_id": str(plan.get("plan_id") or plan_id or ""),
        "plan_status": plan.get("status"),
        "task_decomposition": tasks[:12],
        "dependency_ordering": dependencies[:12],
        "blockers": list(result.blockers),
        "detail": result.detail,
        **_authority_flags(),
    }


def execute_delivery_agent_package(*, session_id: str, plan_id: str | None) -> dict[str, Any]:
    from aethos_core.software_delivery.patch_proposal_service import generate_patch_intent, propose_patch_files

    plan = load_issue_plan_for_session(session_id=session_id)
    if not plan:
        return _blocked(
            role_id="delivery_agent",
            title="DeliveryAgent — patch generation",
            blockers=["issue_plan_missing"],
        )

    fidelity = assess_plan_scope_fidelity(plan=plan)
    if not fidelity.ok:
        return _blocked(
            role_id="delivery_agent",
            title="DeliveryAgent — patch generation",
            blockers=["intent_alignment_scope_fidelity_failed", *fidelity.escalation_reasons],
            detail=fidelity.detail,
        )

    pid = str(plan.get("plan_id") or plan_id or "")
    propose = propose_patch_files(session_id=session_id)
    intent = generate_patch_intent(session_id=session_id) if propose.ok else None
    proposal = load_patch_proposal_for_plan(plan_id=pid) or propose.proposal or {}

    blockers = list(propose.blockers)
    if intent and intent.blockers:
        blockers.extend(intent.blockers)

    work_ok = bool(proposal.get("patch_intent") or proposal.get("unified_diffs"))
    return {
        "agent_role_id": "delivery_agent",
        "title": "DeliveryAgent — patch generation",
        "status": "completed" if work_ok else "partial",
        "work_performed": work_ok,
        "artifact_type": "patch_proposal",
        "plan_id": pid,
        "proposed_files": list(proposal.get("proposed_files") or [])[:12],
        "diff_hunk_count": len(proposal.get("unified_diffs") or []),
        "patch_intent_present": bool(proposal.get("patch_intent")),
        "constraints": ["authorization_envelope", "intent_alignment", "issue_fidelity"],
        "blockers": blockers,
        "detail": (intent.detail if intent else propose.detail) or propose.detail,
        **_authority_flags(),
    }


def execute_verification_agent_package(*, session_id: str, plan_id: str | None) -> dict[str, Any]:
    from aethos_core.software_delivery.workspace_application_store import load_workspace_application_for_plan
    from aethos_core.software_delivery.workspace_verification_store import load_workspace_verification_for_plan

    plan = load_issue_plan_for_session(session_id=session_id)
    if not plan:
        return _blocked(
            role_id="verification_agent",
            title="VerificationAgent — verification package",
            blockers=["issue_plan_missing"],
        )

    pid = str(plan.get("plan_id") or plan_id or "")
    proposal = load_patch_proposal_for_plan(plan_id=pid)
    application = load_workspace_application_for_plan(plan_id=pid)
    existing = load_workspace_verification_for_plan(plan_id=pid)

    planned_checks = [
        "file_existence_verified",
        "static_diff_validated",
        "syntax_check_completed",
    ]
    if application and str(application.get("status") or "") == "applied":
        planned_checks.append("allowlisted_test_completed")

    evidence_gaps: list[str] = []
    if not proposal:
        evidence_gaps.append("patch_proposal_missing")
    if not application:
        evidence_gaps.append("workspace_not_applied")
    if not existing:
        evidence_gaps.append("verification_not_run")

    package = {
        "verification_package_id": f"vpkg-{pid[:8] or 'pending'}",
        "planned_checks": planned_checks,
        "execution_plan": [
            "Inspect workspace tree against patch proposal",
            "Run static diff validation",
            "Classify verification outcome for human gate",
        ],
        "evidence_gaps": evidence_gaps,
        "existing_verification_status": str((existing or {}).get("status") or "not_run"),
    }

    return {
        "agent_role_id": "verification_agent",
        "title": "VerificationAgent — verification package",
        "status": "completed",
        "work_performed": True,
        "artifact_type": "verification_package",
        "plan_id": pid,
        "verification_package": package,
        "blockers": evidence_gaps,
        "detail": "Verification package prepared — execution routes through FIX 125E gate.",
        **_authority_flags(),
    }


def execute_diff_audit_agent_package(*, session_id: str, plan_id: str | None) -> dict[str, Any]:
    plan = load_issue_plan_for_session(session_id=session_id)
    if not plan:
        return _blocked(
            role_id="diff_audit_agent",
            title="DiffAuditAgent — patch review",
            blockers=["issue_plan_missing"],
        )

    pid = str(plan.get("plan_id") or plan_id or "")
    proposal = load_patch_proposal_for_plan(plan_id=pid)
    fidelity = assess_plan_scope_fidelity(plan=plan)
    intended_files = list(plan.get("affected_files") or [])
    proposed_files = list((proposal or {}).get("proposed_files") or [])

    scope_drift: list[str] = []
    for path in proposed_files:
        if intended_files and path not in intended_files:
            scope_drift.append(path)

    blast_radius = str(plan.get("blast_radius") or "unknown")
    audit = {
        "proposal_present": bool(proposal),
        "proposed_file_count": len(proposed_files),
        "scope_drift_files": scope_drift[:12],
        "scope_fidelity_ok": fidelity.ok,
        "blast_radius": blast_radius,
        "human_review_required": True,
    }

    return {
        "agent_role_id": "diff_audit_agent",
        "title": "DiffAuditAgent — patch review",
        "status": "completed" if proposal else "partial",
        "work_performed": bool(proposal),
        "artifact_type": "diff_audit_report",
        "plan_id": pid,
        "diff_audit": audit,
        "blockers": [] if proposal else ["patch_proposal_missing"],
        "detail": "Diff scope audit complete — gates decide apply authority.",
        **_authority_flags(),
    }


def execute_risk_agent_package(*, session_id: str, plan_id: str | None) -> dict[str, Any]:
    from aethos_core.mission_control.mission_authorization.mission_authorization_service import (
        build_mission_authorization,
    )

    plan = load_issue_plan_for_session(session_id=session_id)
    if not plan:
        return _blocked(
            role_id="risk_agent",
            title="RiskAgent — risk scoring",
            blockers=["issue_plan_missing"],
        )

    auth = build_mission_authorization(session_id=session_id)
    envelope = {}
    if auth.ok:
        rows = (auth.mission_authorization.get("sections") or {}).get("bounded_work_envelope") or []
        for row in reversed(rows):
            if row.get("envelope_id") == "bounded-work-envelope":
                envelope = row
                break

    risk = dict(plan.get("risk_assessment") or {})
    allowed_lanes = list(envelope.get("allowed_lanes") or [])
    boundary_ok = bool(envelope.get("authorization_granted"))

    escalation: list[str] = []
    if str(risk.get("risk_tier") or "").lower() in {"high", "critical"}:
        escalation.append("high_risk_tier_requires_human_review")
    if not boundary_ok:
        escalation.append("authorization_envelope_not_granted")
    if "railway_orchestration" in allowed_lanes:
        escalation.append("railway_lane_not_permitted_in_bounded_delivery")

    score = 20
    tier = str(risk.get("risk_tier") or "unknown").lower()
    if tier == "low":
        score += 50
    elif tier == "medium":
        score += 30
    elif tier == "high":
        score += 10
    if boundary_ok:
        score += 20
    score = min(100, score)

    return {
        "agent_role_id": "risk_agent",
        "title": "RiskAgent — risk scoring",
        "status": "completed",
        "work_performed": True,
        "artifact_type": "risk_assessment",
        "plan_id": str(plan.get("plan_id") or plan_id or ""),
        "risk_score": score,
        "risk_tier": risk.get("risk_tier"),
        "authorization_boundary_ok": boundary_ok,
        "allowed_lanes": allowed_lanes,
        "escalation_recommendations": escalation,
        "blockers": escalation,
        "detail": "Risk scoring complete — escalation routes to human review.",
        **_authority_flags(),
    }


EXECUTION_RUNNERS: dict[str, ExecutionRunner] = {
    "planner_agent": execute_planner_agent_package,
    "delivery_agent": execute_delivery_agent_package,
    "verification_agent": execute_verification_agent_package,
    "diff_audit_agent": execute_diff_audit_agent_package,
    "risk_agent": execute_risk_agent_package,
}

assert set(EXECUTION_RUNNERS.keys()) == set(AGENT_EXECUTION_ROLE_IDS)
