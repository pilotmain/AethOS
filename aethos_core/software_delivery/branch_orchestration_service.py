# SPDX-License-Identifier: Apache-2.0
"""FIX 125B — governed branch orchestration service."""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from typing import Any

from aethos_core.software_delivery.branch_orchestration_contract import (
    BRANCH_ARCHIVE_APPROVAL_PHRASE,
    BRANCH_CREATE_APPROVAL_PHRASE,
    BRANCH_RESTORE_APPROVAL_PHRASE,
)
from aethos_core.software_delivery.branch_orchestration_receipts import (
    list_branch_receipts,
    record_branch_receipt,
)
from aethos_core.software_delivery.branch_orchestration_store import (
    append_branch_event,
    load_branch_context_for_plan,
    save_branch_context,
    workspace_path_for_plan,
)
from aethos_core.software_delivery.issue_plan_store import (
    append_plan_event,
    load_issue_plan_for_session,
)

_CREATE_BRANCH_RX = re.compile(r"\bcreate\s+implementation\s+branch\b", re.I)
_BRANCH_STATUS_RX = re.compile(r"\bshow\s+implementation\s+branch\s+status\b", re.I)
_ARCHIVE_BRANCH_RX = re.compile(r"\barchive\s+implementation\s+branch\b", re.I)
_RESTORE_BRANCH_RX = re.compile(r"\brestore\s+implementation\s+branch\b", re.I)
_TIMELINE_RX = re.compile(r"\bshow\s+software\s+delivery\s+timeline\b", re.I)


@dataclass(frozen=True)
class BranchOrchestrationResult:
    ok: bool
    branch_context: dict[str, Any]
    detail: str = ""
    blockers: list[str] = field(default_factory=list)


def is_branch_orchestration_intent(text: str) -> bool:
    raw = (text or "").strip()
    return bool(
        _CREATE_BRANCH_RX.search(raw)
        or _BRANCH_STATUS_RX.search(raw)
        or _ARCHIVE_BRANCH_RX.search(raw)
        or _RESTORE_BRANCH_RX.search(raw)
        or _TIMELINE_RX.search(raw)
    )


def load_branch_orchestration_config() -> dict[str, Any]:
    from aethos_core.config import get_settings

    settings = get_settings()
    return {
        "enabled": bool(getattr(settings, "software_delivery_branch_orchestration_enabled", True)),
        "require_planning_approved": bool(
            getattr(settings, "software_delivery_branch_require_planning_approved", True)
        ),
    }


def _propose_branch_name(*, repository: str, issue_number: int, plan_id: str) -> str:
    slug = repository.split("/")[-1].lower().replace(".", "-")[:24]
    short = (plan_id or "")[-8:] or "plan"
    return f"aethos/sd-{slug}-issue-{issue_number}-{short}"


def _require_approved_plan(session_id: str) -> tuple[dict[str, Any] | None, list[str]]:
    plan = load_issue_plan_for_session(session_id=session_id)
    if not plan:
        return None, ["issue_plan_missing"]
    cfg = load_branch_orchestration_config()
    if cfg["require_planning_approved"] and not plan.get("planning_approved"):
        return plan, ["planning_not_approved"]
    return plan, []


def create_implementation_branch(
    *,
    session_id: str,
    user_text: str,
) -> BranchOrchestrationResult:
    cfg = load_branch_orchestration_config()
    if not cfg["enabled"]:
        return BranchOrchestrationResult(ok=False, branch_context={}, blockers=["branch_orchestration_disabled"])

    plan, blockers = _require_approved_plan(session_id)
    if not plan:
        return BranchOrchestrationResult(
            ok=False,
            branch_context={},
            blockers=blockers,
            detail="Complete FIX 125A planning and approval first.",
        )
    if blockers:
        return BranchOrchestrationResult(ok=False, branch_context={}, blockers=blockers)

    plan_id = str(plan.get("plan_id") or "")
    existing = load_branch_context_for_plan(plan_id=plan_id)
    if existing and str(existing.get("lifecycle_state") or "") == "active":
        return BranchOrchestrationResult(
            ok=True,
            branch_context=existing,
            detail="Implementation branch already active (idempotent).",
        )

    if BRANCH_CREATE_APPROVAL_PHRASE not in (user_text or ""):
        return BranchOrchestrationResult(
            ok=False,
            branch_context=existing or {},
            blockers=["branch_create_approval_required"],
            detail=f"Phrase required: {BRANCH_CREATE_APPROVAL_PHRASE}",
        )

    repository = str(plan.get("repository") or "")
    issue_number = int(plan.get("issue_number") or 0)
    branch_name = _propose_branch_name(
        repository=repository,
        issue_number=issue_number,
        plan_id=plan_id,
    )
    workspace = workspace_path_for_plan(plan_id=plan_id)
    job_id = f"sdjob-{uuid.uuid4().hex[:12]}"

    ctx = {
        "branch_context_id": f"sdbctx-{uuid.uuid4().hex[:12]}",
        "plan_id": plan_id,
        "session_id": session_id,
        "job_id": job_id,
        "repository": repository,
        "issue_number": issue_number,
        "branch_name": branch_name,
        "workspace_path": str(workspace),
        "lifecycle_state": "active",
        "lock_holder": session_id,
        "events": [],
    }
    ctx = save_branch_context(ctx)
    for phase, detail in (
        ("branch_context_created", "One issue → one governed branch context"),
        ("workspace_isolated", f"Workspace path {workspace}"),
        ("branch_create_simulated", "Branch creation simulated — no code modification"),
    ):
        record_branch_receipt(
            plan_id=plan_id,
            phase=phase,
            detail=detail,
            branch_name=branch_name,
            workspace_path=str(workspace),
        )
        ctx = append_branch_event(ctx, action=phase, detail=detail)

    append_plan_event(plan, action="implementation_branch_created", detail=branch_name)
    return BranchOrchestrationResult(
        ok=True,
        branch_context=ctx,
        detail="Governed implementation branch context created (no code changes).",
    )


def archive_implementation_branch(*, session_id: str, user_text: str) -> BranchOrchestrationResult:
    plan = load_issue_plan_for_session(session_id=session_id)
    if not plan:
        return BranchOrchestrationResult(ok=False, branch_context={}, blockers=["issue_plan_missing"])
    ctx = load_branch_context_for_plan(plan_id=str(plan.get("plan_id") or ""))
    if not ctx:
        return BranchOrchestrationResult(ok=False, branch_context={}, blockers=["branch_context_missing"])

    if BRANCH_ARCHIVE_APPROVAL_PHRASE not in (user_text or ""):
        return BranchOrchestrationResult(
            ok=False,
            branch_context=ctx,
            blockers=["branch_archive_approval_required"],
        )

    ctx["lifecycle_state"] = "archived"
    ctx["lock_holder"] = ""
    ctx = save_branch_context(ctx)
    record_branch_receipt(
        plan_id=str(plan.get("plan_id") or ""),
        phase="branch_archived",
        detail="Branch archived — rollback semantics via restore",
        branch_name=str(ctx.get("branch_name") or ""),
    )
    ctx = append_branch_event(ctx, action="branch_archived")
    append_plan_event(plan, action="implementation_branch_archived")
    return BranchOrchestrationResult(ok=True, branch_context=ctx, detail="Branch archived.")


def restore_implementation_branch(*, session_id: str, user_text: str) -> BranchOrchestrationResult:
    plan = load_issue_plan_for_session(session_id=session_id)
    if not plan:
        return BranchOrchestrationResult(ok=False, branch_context={}, blockers=["issue_plan_missing"])
    ctx = load_branch_context_for_plan(plan_id=str(plan.get("plan_id") or ""))
    if not ctx:
        return BranchOrchestrationResult(ok=False, branch_context={}, blockers=["branch_context_missing"])

    if BRANCH_RESTORE_APPROVAL_PHRASE not in (user_text or ""):
        return BranchOrchestrationResult(
            ok=False,
            branch_context=ctx,
            blockers=["branch_restore_approval_required"],
        )

    ctx["lifecycle_state"] = "restored"
    ctx["lock_holder"] = session_id
    ctx = save_branch_context(ctx)
    record_branch_receipt(
        plan_id=str(plan.get("plan_id") or ""),
        phase="branch_restored",
        detail="Branch context restored for continued work",
        branch_name=str(ctx.get("branch_name") or ""),
    )
    ctx = append_branch_event(ctx, action="branch_restored")
    append_plan_event(plan, action="implementation_branch_restored")
    return BranchOrchestrationResult(ok=True, branch_context=ctx, detail="Branch restored.")


def build_software_delivery_timeline(*, session_id: str) -> dict[str, Any]:
    from aethos_core.software_delivery.patch_proposal_receipts import list_patch_receipts
    from aethos_core.software_delivery.patch_proposal_store import load_patch_proposal_for_plan
    from aethos_core.software_delivery.workspace_application_receipts import (
        list_workspace_apply_receipts,
    )
    from aethos_core.software_delivery.workspace_application_store import (
        load_workspace_application_for_plan,
    )
    from aethos_core.software_delivery.workspace_verification_receipts import (
        list_verification_receipts,
    )
    from aethos_core.software_delivery.branch_push_receipts import list_branch_push_receipts
    from aethos_core.software_delivery.branch_push_store import load_branch_push_for_plan
    from aethos_core.software_delivery.github_pr_open_receipts import list_github_pr_open_receipts
    from aethos_core.software_delivery.github_pr_open_store import load_github_pr_open_for_plan
    from aethos_core.software_delivery.github_pr_preflight_receipts import (
        list_github_pr_preflight_receipts,
    )
    from aethos_core.software_delivery.github_pr_preflight_store import (
        load_github_pr_preflight_for_plan,
    )
    from aethos_core.software_delivery.pr_draft_receipts import list_pr_draft_receipts
    from aethos_core.software_delivery.pr_draft_store import load_pr_draft_for_plan
    from aethos_core.software_delivery.workspace_verification_store import (
        load_workspace_verification_for_plan,
    )

    plan = load_issue_plan_for_session(session_id=session_id)
    if not plan:
        return {
            "plan_events": [],
            "branch_receipts": [],
            "branch_events": [],
            "patch_events": [],
            "patch_receipts": [],
            "workspace_verification": None,
            "workspace_verify_events": [],
            "workspace_verify_receipts": [],
            "pr_draft": None,
            "pr_draft_events": [],
            "pr_draft_receipts": [],
            "github_pr_preflight": None,
            "github_pr_preflight_events": [],
            "github_pr_preflight_receipts": [],
            "github_branch_push": None,
            "github_branch_push_events": [],
            "github_branch_push_receipts": [],
            "github_pr_open": None,
            "github_pr_open_events": [],
            "github_pr_open_receipts": [],
        }
    plan_id = str(plan.get("plan_id") or "")
    ctx = load_branch_context_for_plan(plan_id=plan_id)
    proposal = load_patch_proposal_for_plan(plan_id=plan_id)
    application = load_workspace_application_for_plan(plan_id=plan_id)
    verification = load_workspace_verification_for_plan(plan_id=plan_id)
    pr_draft = load_pr_draft_for_plan(plan_id=plan_id)
    github_pf = load_github_pr_preflight_for_plan(plan_id=plan_id)
    branch_push = load_branch_push_for_plan(plan_id=plan_id)
    github_pr_open = load_github_pr_open_for_plan(plan_id=plan_id)
    return {
        "plan": plan,
        "branch_context": ctx,
        "patch_proposal": proposal,
        "workspace_application": application,
        "plan_events": list(plan.get("events") or []),
        "branch_events": list((ctx or {}).get("events") or []),
        "branch_receipts": list_branch_receipts(plan_id=plan_id),
        "patch_events": list((proposal or {}).get("events") or []),
        "patch_receipts": list_patch_receipts(plan_id=plan_id),
        "workspace_apply_events": list((application or {}).get("events") or []),
        "workspace_apply_receipts": list_workspace_apply_receipts(plan_id=plan_id),
        "workspace_verification": verification,
        "workspace_verify_events": list((verification or {}).get("events") or []),
        "workspace_verify_receipts": list_verification_receipts(plan_id=plan_id),
        "pr_draft": pr_draft,
        "pr_draft_events": list((pr_draft or {}).get("events") or []),
        "pr_draft_receipts": list_pr_draft_receipts(plan_id=plan_id),
        "github_pr_preflight": github_pf,
        "github_pr_preflight_events": list((github_pf or {}).get("events") or []),
        "github_pr_preflight_receipts": list_github_pr_preflight_receipts(plan_id=plan_id),
        "github_branch_push": branch_push,
        "github_branch_push_events": list((branch_push or {}).get("events") or []),
        "github_branch_push_receipts": list_branch_push_receipts(plan_id=plan_id),
        "github_pr_open": github_pr_open,
        "github_pr_open_events": list((github_pr_open or {}).get("events") or []),
        "github_pr_open_receipts": list_github_pr_open_receipts(plan_id=plan_id),
    }
