# SPDX-License-Identifier: Apache-2.0
"""FIX 125H — governed branch push service."""

from __future__ import annotations

import os
import re
import uuid
from dataclasses import dataclass, field
from typing import Any

from aethos_core.credentials import get_provider_api_token
from aethos_core.software_delivery.branch_orchestration_store import load_branch_context_for_plan
from aethos_core.software_delivery.branch_push_contract import (
    BRANCH_PUSH_APPROVAL_PHRASE,
    MUTATION_PREVIEW_ACK_PHRASE,
    PROTECTED_DEFAULT_BRANCHES,
)
from aethos_core.software_delivery.branch_push_receipts import record_branch_push_receipt
from aethos_core.software_delivery.branch_push_store import (
    append_push_event,
    load_branch_push_for_plan,
    save_branch_push,
)
from aethos_core.software_delivery.github_git_mutation import push_workspace_files_to_branch
from aethos_core.software_delivery.github_pr_preflight_executor import check_github_auth_scope
from aethos_core.software_delivery.github_pr_preflight_store import (
    github_pr_creation_approved_for_plan,
    load_github_pr_preflight_for_plan,
)
from aethos_core.software_delivery.issue_plan_store import append_plan_event, load_issue_plan_for_session
from aethos_core.software_delivery.pr_draft_store import load_pr_draft_for_plan
from aethos_core.software_delivery.workspace_application_store import load_workspace_application_for_plan
from aethos_core.software_delivery.workspace_verification_store import (
    load_workspace_verification_for_plan,
    workspace_verification_passed,
)

_PUSH_RX = re.compile(
    r"\bpush\s+(?:governed\s+|workspace\s+)?branch\s+to\s+github\b",
    re.I,
)
_STATUS_RX = re.compile(r"\bshow\s+governed\s+branch\s+push\s+status\b", re.I)
_REPORT_RX = re.compile(r"\bshow\s+governed\s+branch\s+push\s+report\b", re.I)

_ACTIVE_BRANCH = frozenset({"active", "restored"})


def _certification_mode() -> bool:
    return os.environ.get("AETHOS_CERTIFICATION_MODE", "").lower() in {"1", "true", "yes"}


@dataclass(frozen=True)
class BranchPushResult:
    ok: bool
    push: dict[str, Any]
    detail: str = ""
    blockers: list[str] = field(default_factory=list)


def is_branch_push_intent(text: str) -> bool:
    raw = (text or "").strip()
    return bool(_PUSH_RX.search(raw) or _STATUS_RX.search(raw) or _REPORT_RX.search(raw))


def load_branch_push_config() -> dict[str, Any]:
    from aethos_core.config import get_settings

    settings = get_settings()
    return {
        "enabled": bool(getattr(settings, "software_delivery_github_branch_push_enabled", True)),
        "default_branch": str(getattr(settings, "software_delivery_github_default_branch", "main")),
    }


def _validate_push_gates(
    *,
    session_id: str,
    user_text: str,
    plan: dict[str, Any],
) -> list[str]:
    blockers: list[str] = []
    plan_id = str(plan.get("plan_id") or "")

    if not github_pr_creation_approved_for_plan(plan_id=plan_id):
        preflight = load_github_pr_preflight_for_plan(plan_id=plan_id)
        if not preflight:
            blockers.append("github_pr_preflight_missing")
        elif str(preflight.get("status") or "") != "preflight_passed":
            blockers.append("github_pr_preflight_not_passed")
        else:
            blockers.append("github_pr_preflight_not_approved")

    if not workspace_verification_passed(plan_id=plan_id):
        blockers.append("workspace_verification_not_passed")

    if not load_pr_draft_for_plan(plan_id=plan_id):
        blockers.append("pr_draft_missing")

    branch = load_branch_context_for_plan(plan_id=plan_id) or {}
    if str(branch.get("lifecycle_state") or "") not in _ACTIVE_BRANCH:
        blockers.append("branch_not_active")

    application = load_workspace_application_for_plan(plan_id=plan_id)
    if not application or str(application.get("status") or "") != "applied":
        blockers.append("workspace_not_applied")

    if BRANCH_PUSH_APPROVAL_PHRASE not in (user_text or ""):
        blockers.append("branch_push_approval_required")
    if MUTATION_PREVIEW_ACK_PHRASE not in (user_text or ""):
        blockers.append("mutation_preview_ack_required")

    return blockers


def push_governed_branch_to_github(*, session_id: str, user_text: str) -> BranchPushResult:
    cfg = load_branch_push_config()
    if not cfg["enabled"]:
        return BranchPushResult(ok=False, push={}, blockers=["branch_push_disabled"])

    plan = load_issue_plan_for_session(session_id=session_id)
    if not plan:
        return BranchPushResult(ok=False, push={}, blockers=["issue_plan_missing"])

    plan_id = str(plan.get("plan_id") or "")
    preflight = load_github_pr_preflight_for_plan(plan_id=plan_id) or {}
    idempotency_key = str(preflight.get("idempotency_key") or "")

    existing = load_branch_push_for_plan(plan_id=plan_id)
    if existing and str(existing.get("status") or "") == "pushed":
        if idempotency_key and existing.get("idempotency_key") == idempotency_key:
            return BranchPushResult(
                ok=True,
                push=existing,
                detail="Branch already pushed (idempotent replay).",
            )

    blockers = _validate_push_gates(session_id=session_id, user_text=user_text, plan=plan)
    if blockers:
        return BranchPushResult(
            ok=False,
            push={},
            blockers=blockers,
            detail="Push gates not satisfied.",
        )

    branch_ctx = load_branch_context_for_plan(plan_id=plan_id) or {}
    application = load_workspace_application_for_plan(plan_id=plan_id) or {}
    draft = load_pr_draft_for_plan(plan_id=plan_id) or {}
    repository = str(plan.get("repository") or "")
    branch_name = str(branch_ctx.get("branch_name") or draft.get("branch_name") or "")
    default_branch = cfg["default_branch"]

    if branch_name in PROTECTED_DEFAULT_BRANCHES or branch_name == default_branch:
        return BranchPushResult(
            ok=False,
            push={},
            blockers=["protected_branch_violation"],
            detail="Cannot push directly to default/protected branch.",
        )

    record_branch_push_receipt(plan_id=plan_id, phase="push_gates_validated", detail="All gates passed")

    auth = check_github_auth_scope(repository=repository)
    record_branch_push_receipt(
        plan_id=plan_id,
        phase="github_scope_rechecked",
        detail=str(auth.get("detail") or ""),
        status="branch_push_success" if auth.get("ok") else "branch_push_failed",
    )
    if not auth.get("ok"):
        return BranchPushResult(ok=False, push={}, blockers=["github_auth_scope"])

    token = get_provider_api_token(provider="github")
    if not token and _certification_mode():
        # Git mutation helpers are simulation-only in certification mode. A
        # non-secret sentinel keeps the gate realistic without live credentials.
        token = "aethos-certification-sentinel"
    if not token:
        return BranchPushResult(ok=False, push={}, blockers=["github_token_missing"])

    files = list(application.get("files_applied") or draft.get("files") or [])
    commit_message = f"chore(aethos): governed software delivery apply ({plan_id})"

    result = push_workspace_files_to_branch(
        token=token,
        repository=repository,
        plan_id=plan_id,
        branch=branch_name,
        files=files,
        default_branch=default_branch,
        commit_message=commit_message,
    )

    if not result.get("ok"):
        return BranchPushResult(
            ok=False,
            push={},
            blockers=["branch_push_failed"],
            detail=str(result.get("error") or result.get("errors") or "push failed"),
        )

    record_branch_push_receipt(plan_id=plan_id, phase="feature_branch_created", detail=str(branch_name))
    record_branch_push_receipt(
        plan_id=plan_id,
        phase="workspace_committed",
        detail=f"{len(result.get('commits') or [])} files",
    )
    record_branch_push_receipt(plan_id=plan_id, phase="feature_branch_pushed", detail=branch_name)

    rollback_plan = dict(preflight.get("rollback_cleanup_plan") or {})
    rollback_plan["branch_push_rollback"] = [
        f"Delete remote branch `{branch_name}` if push must be reverted",
        "Use workspace rollback (125D) for local tree",
        f"Idempotency key `{idempotency_key}` records this push",
    ]

    push_record = existing or {
        "push_id": f"sdbpush-{uuid.uuid4().hex[:12]}",
        "plan_id": plan_id,
        "session_id": session_id,
        "preflight_id": str(preflight.get("preflight_id") or ""),
        "draft_id": str(draft.get("draft_id") or ""),
        "events": [],
    }
    push_record["status"] = "pushed"
    push_record["repository"] = repository
    push_record["branch_name"] = branch_name
    push_record["default_branch"] = default_branch
    push_record["files_pushed"] = list(result.get("files_pushed") or [])
    push_record["head_commit_sha"] = str(result.get("head_commit_sha") or "")
    push_record["idempotency_key"] = idempotency_key
    push_record["commits"] = list(result.get("commits") or [])
    push_record["rollback_cleanup_plan"] = rollback_plan
    push_record["github_pr_created"] = False
    push_record = save_branch_push(push_record)
    push_record = append_push_event(push_record, action="push_completed", detail=branch_name)
    record_branch_push_receipt(
        plan_id=plan_id,
        phase="push_completed",
        push_id=str(push_record.get("push_id") or ""),
    )
    append_plan_event(plan, action="github_branch_pushed", detail=branch_name)

    return BranchPushResult(
        ok=True,
        push=push_record,
        detail=f"Pushed {len(push_record.get('files_pushed') or [])} file(s) to `{branch_name}` (no PR).",
    )


def show_branch_push(*, session_id: str) -> BranchPushResult:
    plan = load_issue_plan_for_session(session_id=session_id)
    if not plan:
        return BranchPushResult(ok=False, push={}, blockers=["issue_plan_missing"])
    push = load_branch_push_for_plan(plan_id=str(plan.get("plan_id") or ""))
    if not push:
        return BranchPushResult(
            ok=False,
            push={},
            blockers=["branch_push_missing"],
            detail="Run `push governed branch to github` after preflight approval.",
        )
    return BranchPushResult(ok=True, push=push)
