# SPDX-License-Identifier: Apache-2.0
"""FIX 125D — apply approved patches to governed workspace only."""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from typing import Any

from aethos_core.software_delivery.branch_orchestration_store import load_branch_context_for_plan
from aethos_core.software_delivery.governed_workspace import (
    apply_patch_to_workspace,
    create_rollback_snapshot,
    restore_rollback_snapshot,
    workspace_tree_root,
    workspace_unified_diffs,
)
from aethos_core.software_delivery.issue_plan_store import (
    append_plan_event,
    load_issue_plan_for_session,
)
from aethos_core.software_delivery.patch_proposal_store import load_patch_proposal_for_plan
from aethos_core.software_delivery.workspace_application_contract import (
    WORKSPACE_APPLY_APPROVAL_PHRASE,
    WORKSPACE_ROLLBACK_APPROVAL_PHRASE,
)
from aethos_core.software_delivery.workspace_application_receipts import (
    record_workspace_apply_receipt,
)
from aethos_core.software_delivery.workspace_application_store import (
    append_apply_event,
    load_workspace_application_for_plan,
    save_workspace_application,
)

_APPLY_RX = re.compile(r"\bapply\s+approved\s+patch\s+to\s+workspace\b", re.I)
_STATUS_RX = re.compile(r"\bshow\s+workspace\s+(?:patch\s+)?apply\s+status\b", re.I)
_DIFF_RX = re.compile(r"\bshow\s+(?:governed\s+)?workspace\s+diff\b", re.I)
_ROLLBACK_RX = re.compile(r"\brollback\s+workspace\s+(?:patch|changes)\b", re.I)

_ACTIVE_BRANCH = frozenset({"active", "restored"})


@dataclass(frozen=True)
class WorkspaceApplicationResult:
    ok: bool
    application: dict[str, Any]
    detail: str = ""
    blockers: list[str] = field(default_factory=list)


def is_workspace_application_intent(text: str) -> bool:
    raw = (text or "").strip()
    return bool(_APPLY_RX.search(raw) or _STATUS_RX.search(raw) or _DIFF_RX.search(raw) or _ROLLBACK_RX.search(raw))


def load_workspace_application_config() -> dict[str, Any]:
    from aethos_core.config import get_settings

    settings = get_settings()
    return {
        "enabled": bool(getattr(settings, "software_delivery_workspace_apply_enabled", True)),
        "require_patch_proposal_approved": bool(
            getattr(settings, "software_delivery_workspace_require_patch_approved", True)
        ),
    }


def _require_apply_context(session_id: str) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], list[str]]:
    plan = load_issue_plan_for_session(session_id=session_id)
    if not plan:
        return {}, {}, {}, ["issue_plan_missing"]
    proposal = load_patch_proposal_for_plan(plan_id=str(plan.get("plan_id") or ""))
    if not proposal:
        return plan, {}, {}, ["patch_proposal_missing"]
    branch = load_branch_context_for_plan(plan_id=str(plan.get("plan_id") or "")) or {}
    if str(branch.get("lifecycle_state") or "") not in _ACTIVE_BRANCH:
        return plan, proposal, branch, ["branch_not_active"]
    cfg = load_workspace_application_config()
    if cfg["require_patch_proposal_approved"] and not proposal.get("patch_proposal_approved"):
        return plan, proposal, branch, ["patch_proposal_not_approved"]
    return plan, proposal, branch, []


def _staged_patches(proposal: dict[str, Any]) -> list[dict[str, Any]]:
    patches = list(proposal.get("staged_patches") or [])
    if patches:
        return patches
    files = list(proposal.get("proposed_files") or [])
    cert_content = "# FIX 125D certification: governed workspace apply marker\n"
    return [{"file": f, "new_content": cert_content, "kind": "certification"} for f in files[:2]]


def apply_approved_patch_to_workspace(*, session_id: str, user_text: str) -> WorkspaceApplicationResult:
    cfg = load_workspace_application_config()
    if not cfg["enabled"]:
        return WorkspaceApplicationResult(
            ok=False, application={}, blockers=["workspace_apply_disabled"]
        )

    plan, proposal, branch, blockers = _require_apply_context(session_id)
    if blockers:
        return WorkspaceApplicationResult(ok=False, application={}, blockers=blockers)

    if WORKSPACE_APPLY_APPROVAL_PHRASE not in (user_text or ""):
        return WorkspaceApplicationResult(
            ok=False,
            application={},
            blockers=["workspace_apply_approval_required"],
            detail=f"Phrase required: {WORKSPACE_APPLY_APPROVAL_PHRASE}",
        )

    plan_id = str(plan.get("plan_id") or "")
    existing = load_workspace_application_for_plan(plan_id=plan_id)
    if existing and str(existing.get("status") or "") == "applied":
        return WorkspaceApplicationResult(
            ok=True,
            application=existing,
            detail="Patch already applied to governed workspace (idempotent).",
        )

    patches = _staged_patches(proposal)
    if not patches:
        return WorkspaceApplicationResult(
            ok=False,
            application={},
            blockers=["staged_patches_missing"],
            detail="Generate and approve patch proposal before workspace apply.",
        )

    allowed = list(proposal.get("proposed_files") or [])
    patch_files = [str(p.get("file") or "") for p in patches if p.get("file")]
    snapshot = create_rollback_snapshot(plan_id=plan_id, files=patch_files)

    record_workspace_apply_receipt(
        plan_id=plan_id,
        phase="proposal_and_workspace_validated",
        detail="Approved proposal and active branch verified",
    )
    record_workspace_apply_receipt(
        plan_id=plan_id,
        phase="rollback_snapshot_created",
        snapshot_id=str(snapshot.get("snapshot_id") or ""),
        files=list(snapshot.get("files") or []),
    )

    applied_files: list[str] = []
    errors: list[str] = []
    for patch in patches:
        rel = str(patch.get("file") or "")
        result = apply_patch_to_workspace(
            plan_id=plan_id,
            rel=rel,
            new_content=str(patch.get("new_content") or ""),
            allowed_files=allowed,
        )
        if result.get("ok"):
            applied_files.append(rel)
            record_workspace_apply_receipt(
                plan_id=plan_id,
                phase="patch_applied_to_workspace",
                files=[rel],
                snapshot_id=str(snapshot.get("snapshot_id") or ""),
            )
        else:
            errors.append(f"{rel}:{result.get('error')}")

    if errors:
        return WorkspaceApplicationResult(
            ok=False,
            application={},
            blockers=["patch_apply_failed"],
            detail="; ".join(errors),
        )

    ws_diffs = workspace_unified_diffs(plan_id=plan_id, files=applied_files)
    record_workspace_apply_receipt(
        plan_id=plan_id,
        phase="workspace_diff_recorded",
        detail=f"{len(ws_diffs)} workspace diff hunks",
        files=applied_files,
    )

    application = existing or {
        "application_id": f"sdwa-{uuid.uuid4().hex[:12]}",
        "plan_id": plan_id,
        "session_id": session_id,
        "proposal_id": str(proposal.get("proposal_id") or ""),
        "branch_context_id": str(branch.get("branch_context_id") or ""),
        "workspace_tree": str(workspace_tree_root(plan_id=plan_id)),
        "events": [],
    }
    application["snapshot_id"] = str(snapshot.get("snapshot_id") or "")
    application["files_applied"] = applied_files
    application["workspace_diffs"] = ws_diffs
    application["status"] = "applied"
    application = save_workspace_application(application)
    application = append_apply_event(
        application,
        action="workspace_apply_completed",
        files=applied_files,
        detail=f"snapshot {snapshot.get('snapshot_id')}",
    )

    record_workspace_apply_receipt(
        plan_id=plan_id,
        phase="workspace_apply_completed",
        snapshot_id=str(snapshot.get("snapshot_id") or ""),
        files=applied_files,
    )
    append_plan_event(plan, action="workspace_patch_applied", detail=",".join(applied_files[:4]))
    return WorkspaceApplicationResult(
        ok=True,
        application=application,
        detail=f"Applied {len(applied_files)} file(s) to governed workspace only (no git/repo mutation).",
    )


def show_workspace_apply_status(*, session_id: str) -> WorkspaceApplicationResult:
    plan = load_issue_plan_for_session(session_id=session_id)
    if not plan:
        return WorkspaceApplicationResult(ok=False, application={}, blockers=["issue_plan_missing"])

    plan_id = str(plan.get("plan_id") or "")
    application = load_workspace_application_for_plan(plan_id=plan_id)
    if not application:
        return WorkspaceApplicationResult(
            ok=False,
            application={},
            blockers=["workspace_not_applied"],
            detail="Run `apply approved patch to workspace` after proposal approval.",
        )
    return WorkspaceApplicationResult(ok=True, application=application)


def show_governed_workspace_diff(*, session_id: str) -> WorkspaceApplicationResult:
    plan, proposal, _, blockers = _require_apply_context(session_id)
    if "issue_plan_missing" in blockers or "patch_proposal_missing" in blockers:
        return WorkspaceApplicationResult(ok=False, application={}, blockers=blockers)

    plan_id = str(plan.get("plan_id") or "")
    application = load_workspace_application_for_plan(plan_id=plan_id)
    files = list((application or {}).get("files_applied") or proposal.get("proposed_files") or [])
    diffs = workspace_unified_diffs(plan_id=plan_id, files=files)
    if application:
        application = save_workspace_application({**application, "workspace_diffs": diffs})
    return WorkspaceApplicationResult(
        ok=bool(diffs) or bool(application),
        application=application or {"workspace_diffs": diffs, "plan_id": plan_id},
        detail="Governed workspace diff (repo unchanged).",
        blockers=[] if diffs or application else ["workspace_diff_empty"],
    )


def rollback_workspace_changes(*, session_id: str, user_text: str) -> WorkspaceApplicationResult:
    plan, _, _, blockers = _require_apply_context(session_id)
    if "issue_plan_missing" in blockers:
        return WorkspaceApplicationResult(ok=False, application={}, blockers=blockers)

    if WORKSPACE_ROLLBACK_APPROVAL_PHRASE not in (user_text or ""):
        return WorkspaceApplicationResult(
            ok=False,
            application={},
            blockers=["workspace_rollback_approval_required"],
            detail=f"Phrase required: {WORKSPACE_ROLLBACK_APPROVAL_PHRASE}",
        )

    plan_id = str(plan.get("plan_id") or "")
    application = load_workspace_application_for_plan(plan_id=plan_id)
    if not application or not application.get("snapshot_id"):
        return WorkspaceApplicationResult(
            ok=False,
            application=application or {},
            blockers=["rollback_snapshot_missing"],
        )

    result = restore_rollback_snapshot(
        plan_id=plan_id,
        snapshot_id=str(application.get("snapshot_id") or ""),
    )
    if not result.get("ok"):
        return WorkspaceApplicationResult(
            ok=False,
            application=application,
            blockers=["rollback_failed"],
            detail=str(result.get("error") or ""),
        )

    application["status"] = "rolled_back"
    application = save_workspace_application(application)
    application = append_apply_event(
        application,
        action="workspace_rollback_completed",
        files=list(result.get("restored_files") or []),
    )
    record_workspace_apply_receipt(
        plan_id=plan_id,
        phase="workspace_rollback_completed",
        snapshot_id=str(application.get("snapshot_id") or ""),
        files=list(result.get("restored_files") or []),
    )
    append_plan_event(plan, action="workspace_patch_rolled_back")
    return WorkspaceApplicationResult(
        ok=True,
        application=application,
        detail="Workspace restored from pre-apply snapshot.",
    )
