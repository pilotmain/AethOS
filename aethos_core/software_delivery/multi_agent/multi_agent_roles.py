# SPDX-License-Identifier: Apache-2.0
"""FIX 127 — bounded software delivery agent role runners (read-only)."""

from __future__ import annotations

from typing import Any, Callable

from aethos_core.software_delivery.branch_orchestration_store import load_branch_context_for_plan
from aethos_core.software_delivery.issue_plan_store import load_issue_plan_for_session
from aethos_core.software_delivery.multi_agent.multi_agent_contract import (
    AGENT_ALLOWED_SCOPES,
    AGENT_FORBIDDEN_SCOPES,
    BOUNDED_AGENT_ROLE_IDS,
)
from aethos_core.software_delivery.patch_proposal_store import load_patch_proposal_for_plan
from aethos_core.software_delivery.pr_draft_store import load_pr_draft_for_plan
from aethos_core.software_delivery.software_delivery_phase_2_contract import (
    SOFTWARE_DELIVERY_LOOP_ORDER,
)
from aethos_core.software_delivery.workspace_verification_store import (
    load_workspace_verification_for_plan,
)

RoleRunner = Callable[..., dict[str, Any]]


def _base_result(*, role_id: str, title: str, findings: list[str], recommendations: list[str]) -> dict[str, Any]:
    return {
        "agent_role_id": role_id,
        "title": title,
        "status": "completed",
        "findings": findings,
        "recommendations": recommendations,
        "allowed_scopes": list(AGENT_ALLOWED_SCOPES),
        "forbidden_scopes": list(AGENT_FORBIDDEN_SCOPES),
        "mutation_performed": False,
        "self_authorizing": False,
    }


def run_planner_agent(*, session_id: str, plan_id: str) -> dict[str, Any]:
    plan = load_issue_plan_for_session(session_id=session_id) or {}
    events = [str(e.get("action") or "") for e in plan.get("events") or []]
    completed: list[str] = []
    if "issue_analyzed" in events or plan.get("status"):
        completed.append("issue_intake")
    if "planning_approved" in events or str(plan.get("status") or "") == "planning_approved":
        completed.append("implementation_plan")
    if load_branch_context_for_plan(plan_id=plan_id):
        completed.append("implementation_branch")
    pending = [s for s in SOFTWARE_DELIVERY_LOOP_ORDER if s not in completed and s != "human_review"]
    return _base_result(
        role_id="planner_agent",
        title="PlannerAgent — loop position",
        findings=[
            f"Plan `{plan_id}` status: **{plan.get('status', 'unknown')}**",
            f"Completed stages: {', '.join(completed) or 'none'}",
        ],
        recommendations=[
            f"Next governed stages (frozen loop): {', '.join(pending[:4]) or 'human_review'}",
            "Do not skip verification or preflight before GitHub mutations.",
        ],
    )


def run_reviewer_agent(*, session_id: str, plan_id: str) -> dict[str, Any]:
    draft = load_pr_draft_for_plan(plan_id=plan_id)
    checklist = list((draft or {}).get("checklist") or [])
    human = list((draft or {}).get("human_review_requirements") or [])
    return _base_result(
        role_id="reviewer_agent",
        title="ReviewerAgent — human review readiness",
        findings=[
            f"PR draft: **{'present' if draft else 'missing'}**",
            f"Checklist items: **{len(checklist)}**",
        ],
        recommendations=[
            "Human reviewer must confirm verification and read workspace diff.",
            "Merge only via GitHub UI — not through software delivery lane.",
            *([f"- {item}" for item in human[:4]] if human else ["- Create PR draft (125F) before review briefing"]),
        ],
    )


def run_verification_agent(*, session_id: str, plan_id: str) -> dict[str, Any]:
    verification = load_workspace_verification_for_plan(plan_id=plan_id)
    status = str((verification or {}).get("status") or "not_run")
    classification = (verification or {}).get("classification") or {}
    return _base_result(
        role_id="verification_agent",
        title="VerificationAgent — workspace verification",
        findings=[
            f"Verification status: **{status}**",
            f"Summary: {classification.get('summary') or 'n/a'}",
        ],
        recommendations=[
            "Run `run workspace verification` if not passed.",
            "PR draft remains blocked until verification passes (125E gate).",
        ],
    )


def run_risk_agent(*, session_id: str, plan_id: str) -> dict[str, Any]:
    plan = load_issue_plan_for_session(session_id=session_id) or {}
    risk = plan.get("risk_assessment") or {}
    return _base_result(
        role_id="risk_agent",
        title="RiskAgent — delivery risk",
        findings=[
            f"Risk tier: **{risk.get('risk_tier', 'unknown')}**",
            f"Blast radius: **{plan.get('blast_radius', '')}**",
            f"Repository: **{plan.get('repository', '')}**",
        ],
        recommendations=[
            "Confirm blast radius acceptable before workspace apply.",
            "Keep infra deploy in Railway lane — separate from software delivery.",
        ],
    )


def run_diff_audit_agent(*, session_id: str, plan_id: str) -> dict[str, Any]:
    proposal = load_patch_proposal_for_plan(plan_id=plan_id)
    files = list((proposal or {}).get("proposed_files") or [])
    diffs = list((proposal or {}).get("unified_diffs") or [])
    return _base_result(
        role_id="diff_audit_agent",
        title="DiffAuditAgent — patch proposal audit",
        findings=[
            f"Proposal: **{'present' if proposal else 'missing'}**",
            f"Proposed files: **{len(files)}**",
            f"Diff hunks: **{len(diffs)}**",
        ],
        recommendations=[
            "Review `show patch diff preview` before workspace apply.",
            "Approve patch proposal with exact phrase before apply (125D).",
        ],
    )


ROLE_RUNNERS: dict[str, RoleRunner] = {
    "planner_agent": run_planner_agent,
    "reviewer_agent": run_reviewer_agent,
    "verification_agent": run_verification_agent,
    "risk_agent": run_risk_agent,
    "diff_audit_agent": run_diff_audit_agent,
}

assert set(ROLE_RUNNERS.keys()) == set(BOUNDED_AGENT_ROLE_IDS)
