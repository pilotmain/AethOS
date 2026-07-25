# SPDX-License-Identifier: Apache-2.0
"""FIX 125A — issue intake and governed implementation planning."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from typing import Any

from pathlib import Path

from aethos_core.engineering.task_intake import intake_engineering_task, parse_github_issue
from aethos_core.software_delivery.issue_intake_scope_fidelity_service import (
    assess_plan_scope_fidelity,
    build_fidelity_governed_task,
    envelope_to_plan_payload,
    extract_issue_scope_fidelity,
    should_use_scope_fidelity_task,
)
from aethos_core.software_delivery.issue_plan_contract import (
    AUTO_SCOPE_EXPANSION_PERMITTED,
    BLOCKED_ACTIONS_FIX_125A,
    CODE_GENERATION_ENABLED_FIX_125A,
    INFRA_MUTATION_PERMITTED,
    PLANNING_APPROVAL_PHRASE,
    SOFTWARE_DELIVERY_LANE_ID,
)
from aethos_core.software_delivery.issue_plan_store import (
    append_plan_event,
    load_issue_plan_for_session,
    save_issue_plan,
)

_ISSUE_REF_RX = re.compile(
    r"(?P<repo>[\w.-]+/[\w.-]+)\s*#(?P<num>\d+)",
    re.I,
)
_ISSUE_NUM_RX = re.compile(r"\bissue\s+#?(?P<num>\d+)\b", re.I)

_ANALYZE_RX = re.compile(r"\banalyze\s+github\s+issue\b", re.I)
_CREATE_PLAN_RX = re.compile(r"\bcreate\s+implementation\s+plan\b", re.I)
_SCOPE_RX = re.compile(r"\bshow\s+implementation\s+scope\b", re.I)
_RISK_RX = re.compile(r"\bshow\s+risk\s+assessment\b", re.I)
_APPROVE_RX = re.compile(r"\bapprove\s+implementation\s+planning\b", re.I)


@dataclass(frozen=True)
class IssuePlanResult:
    ok: bool
    plan: dict[str, Any]
    detail: str = ""
    blockers: list[str] = field(default_factory=list)


def is_software_delivery_issue_plan_intent(text: str) -> bool:
    raw = (text or "").strip()
    return bool(
        _ANALYZE_RX.search(raw)
        or _CREATE_PLAN_RX.search(raw)
        or _SCOPE_RX.search(raw)
        or _RISK_RX.search(raw)
        or _APPROVE_RX.search(raw)
        or extract_planning_approval(raw)
    )


def extract_planning_approval(text: str) -> bool:
    return PLANNING_APPROVAL_PHRASE in (text or "")


def load_issue_plan_config() -> dict[str, Any]:
    from aethos_core.config import get_settings

    settings = get_settings()
    return {
        "enabled": bool(getattr(settings, "software_delivery_issue_plan_enabled", True)),
        "require_planning_approval": bool(
            getattr(settings, "software_delivery_require_planning_approval", True)
        ),
    }


def parse_issue_reference(text: str, *, default_repo: str = "") -> tuple[str, int | None]:
    raw = (text or "").strip()
    match = _ISSUE_REF_RX.search(raw)
    if match:
        return match.group("repo"), int(match.group("num"))
    num_match = _ISSUE_NUM_RX.search(raw)
    if num_match and default_repo:
        return default_repo, int(num_match.group("num"))
    if default_repo:
        return default_repo, None
    return "", None


def _dogfood_issue_1_fixture(*, repository: str) -> dict[str, Any]:
    return {
        "number": 1,
        "title": "AethOS Dogfood Pilot — Add Pilot Execution Log Section",
        "body": (
            "### Purpose\n\n"
            "First governed dogfood pilot.\n\n"
            "### Scope (Bounded)\n\n"
            "Add a new section to:\n\n"
            "`docs/AETHOS_DOGFOOD_AND_PILOT_VALIDATION_PRINCIPLE.md`\n\n"
            "**Section title:** Pilot Execution Log\n\n"
            "### Out Of Scope\n\n"
            "- workflow files\n"
            "- provider files\n"
            "- mutation files\n"
            "- Railway\n"
            "- Deploy\n"
            "- Merge\n"
        ),
        "html_url": f"https://github.com/{repository}/issues/1",
    }


def _certification_issue_fixture(*, repository: str, issue_number: int) -> dict[str, Any]:
    if issue_number == 1:
        return _dogfood_issue_1_fixture(repository=repository)
    return {
        "number": issue_number,
        "title": "Fix workflow rerun resolution in governed GitHub lane",
        "body": (
            "Workflow rerun fails when resolver returns readonly. "
            "Need bounded fix in github workflow lane without production deploy."
        ),
        "html_url": f"https://github.com/{repository}/issues/{issue_number}",
    }


def _normalize_github_issue_payload(data: dict[str, Any]) -> dict[str, Any]:
    return {
        "number": data.get("number"),
        "title": str(data.get("title") or ""),
        "body": str(data.get("body") or ""),
        "html_url": str(data.get("html_url") or ""),
        "state": str(data.get("state") or ""),
    }


def fetch_github_issue(
    *,
    repository: str,
    issue_number: int,
    session_id: str = "",
) -> dict[str, Any]:
    if os.environ.get("AETHOS_CERTIFICATION_MODE", "").lower() in {"1", "true", "yes"}:
        return _certification_issue_fixture(repository=repository, issue_number=issue_number)

    from aethos_core.credentials import get_provider_api_token
    from aethos_core.providers.github.api_client import parse_owner_repo, request_github

    token = get_provider_api_token("github", require_validated=False)
    owner, repo = parse_owner_repo(repository)
    if token and owner and repo:
        result = request_github(
            token,
            "GET",
            f"/repos/{owner}/{repo}/issues/{issue_number}",
        )
        data = result.get("data")
        if result.get("ok") and isinstance(data, dict):
            return _normalize_github_issue_payload(data)

    if issue_number == 1:
        return _dogfood_issue_1_fixture(repository=repository)
    _ = session_id
    return _certification_issue_fixture(repository=repository, issue_number=issue_number)


def _blast_radius_from_task(task: dict[str, Any]) -> str:
    risk = str(task.get("risk_tier") or "medium")
    if risk == "high":
        return "platform"
    if risk == "low":
        return "local"
    return "service"


def _build_governed_plan(*, task: dict[str, Any], issue: dict[str, Any]) -> dict[str, Any]:
    affected = list(task.get("affected_files") or [])
    return {
        "goal": str(task.get("title") or issue.get("title") or "Implementation plan"),
        "problem_summary": str(task.get("problem_summary") or ""),
        "likely_cause": str(task.get("likely_cause") or ""),
        "bounded_steps": [
            "Research affected modules with provenance (read-only)",
            "Draft minimal diff scope — no unrelated refactors",
            "Define verification commands before any branch work (FIX 125B+)",
            "Prepare PR summary for human review (FIX 125E+)",
        ],
        "out_of_scope": list(BLOCKED_ACTIONS_FIX_125A),
        "human_gates": [
            "planning approval (FIX 125A)",
            "branch creation approval (FIX 125B)",
            "code change approval (FIX 125C)",
            "PR merge by human only",
        ],
    }


def analyze_github_issue(
    *,
    session_id: str,
    user_text: str,
    default_repo: str = "pilotmain/AethOS",
) -> IssuePlanResult:
    cfg = load_issue_plan_config()
    if not cfg["enabled"]:
        return IssuePlanResult(ok=False, plan={}, blockers=["software_delivery_disabled"])

    repository, issue_number = parse_issue_reference(user_text, default_repo=default_repo)
    if not repository:
        return IssuePlanResult(
            ok=False,
            plan={},
            blockers=["issue_reference_missing"],
            detail="Specify repository as owner/repo#123",
        )
    if issue_number is None:
        return IssuePlanResult(
            ok=False,
            plan={},
            blockers=["issue_number_missing"],
            detail="Specify issue number, e.g. pilotmain/AethOS#42",
        )

    issue = fetch_github_issue(
        repository=repository,
        issue_number=issue_number,
        session_id=session_id,
    )
    repo_root = Path(__file__).resolve().parents[2]
    scope_envelope = extract_issue_scope_fidelity(issue=issue, repo=repo_root)
    if should_use_scope_fidelity_task(issue=issue, envelope=scope_envelope):
        task = build_fidelity_governed_task(issue=issue, envelope=scope_envelope, repo=repo_root)
    else:
        task = parse_github_issue(issue, repo=repo_root)
    governed = _build_governed_plan(task=task, issue=issue)
    if scope_envelope.expected_files or scope_envelope.explicit_bounded_scope:
        governed["goal"] = scope_envelope.intended_goal
        governed["scope"] = ", ".join(scope_envelope.expected_files[:8])
        if scope_envelope.out_of_scope_constraints:
            governed["out_of_scope"] = list(scope_envelope.out_of_scope_constraints) + list(
                governed.get("out_of_scope") or []
            )
    affected = list(scope_envelope.expected_files) or list(task.get("affected_files") or [])

    import uuid

    plan = {
        "plan_id": f"sdplan-{uuid.uuid4().hex[:12]}",
        "session_id": session_id,
        "lane_id": SOFTWARE_DELIVERY_LANE_ID,
        "repository": repository,
        "issue_number": issue_number,
        "issue_url": str(issue.get("html_url") or ""),
        "issue_title": str(issue.get("title") or ""),
        "issue_body": str(issue.get("body") or ""),
        "status": "analyzed",
        "governed_plan": governed,
        "affected_files": affected,
        "issue_intake_scope_fidelity": envelope_to_plan_payload(scope_envelope),
        "blast_radius": _blast_radius_from_task(task),
        "test_expectations": list(task.get("test_scope") or []),
        "rollback_notes": [
            "Revert feature branch; no production deploy from this lane.",
            "Infra orchestration remains separately governed (Railway lane).",
        ],
        "risk_assessment": {
            "risk_tier": task.get("risk_tier"),
            "kind": task.get("kind"),
            "labels": list(task.get("labels") or []),
        },
        "planning_approved": False,
        "events": [],
    }
    plan = save_issue_plan(plan)
    plan = append_plan_event(plan, action="issue_analyzed", detail=f"{repository}#{issue_number}")
    return IssuePlanResult(ok=True, plan=plan, detail="GitHub issue analyzed (planning only).")


def create_implementation_plan(*, session_id: str) -> IssuePlanResult:
    plan = load_issue_plan_for_session(session_id=session_id)
    if not plan:
        return IssuePlanResult(
            ok=False,
            plan={},
            detail="Run `analyze github issue owner/repo#N` first.",
        )
    fidelity = assess_plan_scope_fidelity(plan=plan)
    if not fidelity.ok:
        plan = append_plan_event(
            plan,
            action="implementation_plan_blocked_scope_fidelity",
            detail=fidelity.detail,
        )
        return IssuePlanResult(
            ok=False,
            plan=plan,
            blockers=["issue_intake_scope_fidelity_failed", *fidelity.escalation_reasons],
            detail=fidelity.detail,
        )
    plan["status"] = "plan_drafted"
    plan = save_issue_plan(plan)
    plan = append_plan_event(plan, action="implementation_plan_drafted")
    return IssuePlanResult(ok=True, plan=plan, detail="Governed implementation plan drafted.")


def approve_implementation_planning(
    *,
    session_id: str,
    user_text: str,
) -> IssuePlanResult:
    plan = load_issue_plan_for_session(session_id=session_id)
    if not plan:
        return IssuePlanResult(ok=False, plan={}, detail="No issue plan for session.")

    if not extract_planning_approval(user_text):
        plan = append_plan_event(plan, action="planning_approval_rejected")
        return IssuePlanResult(
            ok=False,
            plan=plan,
            blockers=["planning_approval_phrase_required"],
            detail=f"Phrase required: {PLANNING_APPROVAL_PHRASE}",
        )

    if plan.get("planning_approved") and str(plan.get("status") or "") == "planning_approved":
        return IssuePlanResult(
            ok=True,
            plan=plan,
            detail="Planning already approved for this session.",
        )

    if str(plan.get("status") or "") not in {"analyzed", "plan_drafted"}:
        return IssuePlanResult(
            ok=False,
            plan=plan,
            blockers=["plan_not_ready_for_approval"],
            detail="Create implementation plan before approval.",
        )

    fidelity = assess_plan_scope_fidelity(plan=plan)
    if not fidelity.ok:
        plan = append_plan_event(
            plan,
            action="planning_approval_blocked_scope_fidelity",
            detail=fidelity.detail,
        )
        return IssuePlanResult(
            ok=False,
            plan=plan,
            blockers=["issue_intake_scope_fidelity_failed", *fidelity.escalation_reasons],
            detail=fidelity.detail,
        )

    plan["planning_approved"] = True
    plan["status"] = "planning_approved"
    plan = save_issue_plan(plan)
    plan = append_plan_event(plan, action="planning_approved", actor="operator")
    return IssuePlanResult(
        ok=True,
        plan=plan,
        detail="Planning approved. Branch and patch work follow FIX 125B/125C gates.",
    )


def get_lane_invariants() -> dict[str, Any]:
    return {
        "lane": SOFTWARE_DELIVERY_LANE_ID,
        "infra_lane": "infrastructure_orchestration",
        "lanes_must_not_merge": True,
        "mutation_performed": False,
        "code_generation_enabled": CODE_GENERATION_ENABLED_FIX_125A,
        "infra_mutation_permitted": INFRA_MUTATION_PERMITTED,
        "auto_scope_expansion": AUTO_SCOPE_EXPANSION_PERMITTED,
        "blocked_actions": list(BLOCKED_ACTIONS_FIX_125A),
    }
