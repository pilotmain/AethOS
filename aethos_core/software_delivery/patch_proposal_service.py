# SPDX-License-Identifier: Apache-2.0
"""FIX 125C — governed patch proposal service (proposal only, no writes)."""

from __future__ import annotations

import os
import re
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from aethos_core.engineering.patch_engine import generate_patch_proposal
from aethos_core.engineering.task_intake import intake_engineering_task
from aethos_core.software_delivery.branch_orchestration_store import load_branch_context_for_plan
from aethos_core.software_delivery.issue_plan_store import (
    append_plan_event,
    load_issue_plan_for_session,
)
from aethos_core.software_delivery.patch_proposal_contract import (
    PATCH_PROPOSAL_APPROVAL_PHRASE,
)
from aethos_core.software_delivery.patch_proposal_receipts import record_patch_receipt
from aethos_core.software_delivery.patch_proposal_store import (
    append_proposal_event,
    load_patch_proposal_for_plan,
    save_patch_proposal,
)

_PROPOSE_FILES_RX = re.compile(
    r"\bpropose\s+(?:patch\s+files|files\s+to\s+change)\b",
    re.I,
)
_GENERATE_INTENT_RX = re.compile(r"\bgenerate\s+patch\s+(?:intent|proposal)\b", re.I)
_DIFF_PREVIEW_RX = re.compile(r"\bshow\s+(?:patch\s+)?diff\s+preview\b", re.I)
_APPROVE_PROPOSAL_RX = re.compile(r"\bapprove\s+patch\s+proposal\b", re.I)
_PROPOSAL_STATUS_RX = re.compile(r"\bshow\s+patch\s+proposal\s+status\b", re.I)

_ACTIVE_BRANCH_STATES = frozenset({"active", "restored"})


@dataclass(frozen=True)
class PatchProposalResult:
    ok: bool
    proposal: dict[str, Any]
    detail: str = ""
    blockers: list[str] = field(default_factory=list)


def is_patch_proposal_intent(text: str) -> bool:
    raw = (text or "").strip()
    return bool(
        _PROPOSE_FILES_RX.search(raw)
        or _GENERATE_INTENT_RX.search(raw)
        or _DIFF_PREVIEW_RX.search(raw)
        or _APPROVE_PROPOSAL_RX.search(raw)
        or _PROPOSAL_STATUS_RX.search(raw)
    )


def load_patch_proposal_config() -> dict[str, Any]:
    from aethos_core.config import get_settings

    settings = get_settings()
    return {
        "enabled": bool(getattr(settings, "software_delivery_patch_proposal_enabled", True)),
        "require_planning_approved": bool(
            getattr(settings, "software_delivery_patch_require_planning_approved", True)
        ),
        "require_active_branch": bool(
            getattr(settings, "software_delivery_patch_require_active_branch", True)
        ),
    }


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _require_plan_and_branch(session_id: str) -> tuple[dict[str, Any] | None, dict[str, Any] | None, list[str]]:
    cfg = load_patch_proposal_config()
    plan = load_issue_plan_for_session(session_id=session_id)
    if not plan:
        return None, None, ["issue_plan_missing"]
    if cfg["require_planning_approved"] and not plan.get("planning_approved"):
        return plan, None, ["planning_not_approved"]
    ctx = load_branch_context_for_plan(plan_id=str(plan.get("plan_id") or ""))
    if cfg["require_active_branch"]:
        if not ctx:
            return plan, None, ["branch_context_missing"]
        if str(ctx.get("lifecycle_state") or "") not in _ACTIVE_BRANCH_STATES:
            return plan, ctx, ["branch_not_active"]
    return plan, ctx, []


def _certification_proposal_fixture(*, plan: dict[str, Any], branch: dict[str, Any] | None) -> dict[str, Any]:
    files = [
        "aethos_core/providers/github/shared/workflow_resolution.py",
        "aethos_core/providers/github/operations/mutations_api.py",
    ]
    diffs = [
        {
            "file": files[0],
            "diff": (
                f"--- a/{files[0]}\n"
                f"+++ b/{files[0]}\n"
                "@@ -1,3 +1,4 @@\n"
                "+# FIX 125C certification: governed patch intent (no write)\n"
            ),
            "lines_changed": 1,
        }
    ]
    cert_patches = [
        {
            "file": files[0],
            "new_content": (
                "# FIX 125C/125D certification marker\n"
                "GOVERNED_WORKSPACE_PATCH_MARKER = \"certification_simulation\"\n"
            ),
            "kind": "certification",
        }
    ]
    return {
        "ok": True,
        "proposed_files": files,
        "staged_patches": cert_patches,
        "patch_intent": {
            "intent_id": f"sdpi-cert-{uuid.uuid4().hex[:8]}",
            "summary": "Align workflow rerun resolution (certification simulation)",
            "bounded_scope": files,
            "branch_name": str((branch or {}).get("branch_name") or ""),
            "workspace_path": str((branch or {}).get("workspace_path") or ""),
            "issue_title": str(plan.get("issue_title") or ""),
        },
        "unified_diffs": diffs,
        "diff_intelligence": {"risk_tier": "E2_branch_diff", "total_diff_lines": 1},
        "execution_mode": "certification_simulation",
    }


def _build_task_from_plan(plan: dict[str, Any]) -> dict[str, Any]:
    gp = plan.get("governed_plan") or {}
    body = f"{plan.get('issue_title') or ''}\n{gp.get('problem_summary') or ''}"
    task = intake_engineering_task(body, repo=_repo_root())
    fidelity = plan.get("issue_intake_scope_fidelity") or {}
    plan_files = list(fidelity.get("expected_files") or plan.get("affected_files") or [])
    if plan_files:
        task["affected_files"] = plan_files
    if fidelity.get("expected_files"):
        intended_goal = str(fidelity.get("intended_goal") or plan.get("issue_title") or "")
        task["kind"] = "bounded_issue_scope"
        task["proposed_fix"] = intended_goal
        task["title"] = intended_goal or task.get("title")
        task["source"] = "issue_intake_scope_fidelity"
        task["raw_request"] = str(plan.get("issue_body") or body)[:500]
    return task


def _merge_proposed_files(plan: dict[str, Any], task: dict[str, Any]) -> list[str]:
    files: list[str] = []
    for path in list(plan.get("affected_files") or []) + list(task.get("affected_files") or []):
        if path and path not in files:
            files.append(path)
    repo = _repo_root()
    files = [f for f in files if (repo / f).is_file()]
    return files[:12]


def propose_patch_files(*, session_id: str) -> PatchProposalResult:
    cfg = load_patch_proposal_config()
    if not cfg["enabled"]:
        return PatchProposalResult(ok=False, proposal={}, blockers=["patch_proposal_disabled"])

    plan, branch, blockers = _require_plan_and_branch(session_id)
    if blockers:
        return PatchProposalResult(
            ok=False,
            proposal={},
            blockers=blockers,
            detail="Complete plan → branch before patch proposal.",
        )
    assert plan is not None

    plan_id = str(plan.get("plan_id") or "")
    task = _build_task_from_plan(plan)
    proposed = _merge_proposed_files(plan, task)

    proposal = load_patch_proposal_for_plan(plan_id=plan_id) or {
        "proposal_id": f"sdpp-{uuid.uuid4().hex[:12]}",
        "plan_id": plan_id,
        "session_id": session_id,
        "branch_context_id": str((branch or {}).get("branch_context_id") or ""),
        "status": "files_proposed",
        "proposed_files": [],
        "patch_intent": {},
        "unified_diffs": [],
        "patch_proposal_approved": False,
        "events": [],
    }
    proposal["proposed_files"] = proposed
    proposal["status"] = "files_proposed"
    proposal = save_patch_proposal(proposal)

    record_patch_receipt(
        plan_id=plan_id,
        phase="plan_and_branch_inspected",
        detail="Inspected approved plan and branch context",
        proposal_id=str(proposal.get("proposal_id") or ""),
    )
    record_patch_receipt(
        plan_id=plan_id,
        phase="patch_files_proposed",
        detail=f"{len(proposed)} files in bounded scope",
        proposal_id=str(proposal.get("proposal_id") or ""),
        files=proposed,
    )
    proposal = append_proposal_event(
        proposal,
        action="patch_files_proposed",
        detail=", ".join(proposed[:6]),
    )
    append_plan_event(plan, action="patch_files_proposed", detail=str(len(proposed)))
    return PatchProposalResult(
        ok=bool(proposed),
        proposal=proposal,
        detail=f"Proposed {len(proposed)} file(s) for bounded patch (no writes).",
        blockers=[] if proposed else ["no_files_in_scope"],
    )


def generate_patch_intent(*, session_id: str) -> PatchProposalResult:
    plan, branch, blockers = _require_plan_and_branch(session_id)
    if blockers:
        return PatchProposalResult(ok=False, proposal={}, blockers=blockers)
    assert plan is not None

    plan_id = str(plan.get("plan_id") or "")
    proposal = load_patch_proposal_for_plan(plan_id=plan_id)
    if not proposal or not proposal.get("proposed_files"):
        return PatchProposalResult(
            ok=False,
            proposal=proposal or {},
            blockers=["patch_files_not_proposed"],
            detail="Run `propose patch files` first.",
        )

    cert_mode = os.environ.get("AETHOS_CERTIFICATION_MODE", "").lower() in {"1", "true", "yes"}
    if cert_mode:
        generated = _certification_proposal_fixture(plan=plan, branch=branch)
    else:
        task = _build_task_from_plan(plan)
        user_request = str((plan.get("governed_plan") or {}).get("goal") or plan.get("issue_title") or "")
        generated = generate_patch_proposal(
            _repo_root(),
            user_request=user_request,
            task=task,
            target_files=list(proposal.get("proposed_files") or []),
        )

    intent = {
        "intent_id": f"sdpi-{uuid.uuid4().hex[:12]}",
        "summary": generated.get("patch_summary") or "Bounded patch intent",
        "risk_tier": generated.get("risk_tier") or "unknown",
        "validation_steps": list(generated.get("validation_steps") or []),
        "rollback_strategy": generated.get("rollback_strategy") or "Revert branch; no deploy.",
        "branch_name": str((branch or {}).get("branch_name") or ""),
        "workspace_path": str((branch or {}).get("workspace_path") or ""),
        "bounded_scope": list(proposal.get("proposed_files") or []),
        "files_patched": list(generated.get("files_patched") or []),
    }
    proposal["patch_intent"] = intent
    proposal["unified_diffs"] = list(generated.get("unified_diffs") or [])
    proposal["staged_patches"] = list(generated.get("staged_patches") or generated.get("patches") or [])
    proposal["diff_intelligence"] = generated.get("diff_intelligence") or {}
    proposal["status"] = "intent_generated"
    proposal = save_patch_proposal(proposal)

    record_patch_receipt(
        plan_id=plan_id,
        phase="patch_intent_generated",
        detail=str(intent.get("summary") or ""),
        proposal_id=str(proposal.get("proposal_id") or ""),
        files=list(intent.get("bounded_scope") or []),
    )
    proposal = append_proposal_event(proposal, action="patch_intent_generated")
    append_plan_event(plan, action="patch_intent_generated")
    return PatchProposalResult(
        ok=generated.get("ok", True),
        proposal=proposal,
        detail="Patch intent generated (preview only — no file writes).",
    )


def show_patch_diff_preview(*, session_id: str) -> PatchProposalResult:
    plan, _, blockers = _require_plan_and_branch(session_id)
    if blockers:
        return PatchProposalResult(ok=False, proposal={}, blockers=blockers)
    assert plan is not None

    proposal = load_patch_proposal_for_plan(plan_id=str(plan.get("plan_id") or ""))
    if not proposal or not proposal.get("unified_diffs"):
        return PatchProposalResult(
            ok=False,
            proposal=proposal or {},
            blockers=["patch_intent_not_generated"],
            detail="Run `generate patch intent` first.",
        )

    proposal["status"] = "diff_previewed"
    proposal = save_patch_proposal(proposal)
    record_patch_receipt(
        plan_id=str(plan.get("plan_id") or ""),
        phase="diff_preview_recorded",
        proposal_id=str(proposal.get("proposal_id") or ""),
        detail=f"{len(proposal.get('unified_diffs') or [])} diff hunks",
    )
    proposal = append_proposal_event(proposal, action="diff_preview_recorded")
    return PatchProposalResult(ok=True, proposal=proposal, detail="Diff preview ready.")


def approve_patch_proposal(*, session_id: str, user_text: str) -> PatchProposalResult:
    plan, _, blockers = _require_plan_and_branch(session_id)
    if blockers:
        return PatchProposalResult(ok=False, proposal={}, blockers=blockers)
    assert plan is not None

    proposal = load_patch_proposal_for_plan(plan_id=str(plan.get("plan_id") or ""))
    if not proposal:
        return PatchProposalResult(ok=False, proposal={}, blockers=["patch_proposal_missing"])

    if PATCH_PROPOSAL_APPROVAL_PHRASE not in (user_text or ""):
        return PatchProposalResult(
            ok=False,
            proposal=proposal,
            blockers=["patch_proposal_approval_required"],
            detail=f"Phrase required: {PATCH_PROPOSAL_APPROVAL_PHRASE}",
        )

    if not proposal.get("unified_diffs"):
        return PatchProposalResult(
            ok=False,
            proposal=proposal,
            blockers=["diff_preview_required"],
            detail="Generate patch intent and review diff preview before approval.",
        )

    if proposal.get("patch_proposal_approved"):
        return PatchProposalResult(
            ok=True,
            proposal=proposal,
            detail="Patch proposal already approved (idempotent).",
        )

    proposal["patch_proposal_approved"] = True
    proposal["status"] = "proposal_approved"
    proposal = save_patch_proposal(proposal)
    record_patch_receipt(
        plan_id=str(plan.get("plan_id") or ""),
        phase="patch_proposal_approved",
        proposal_id=str(proposal.get("proposal_id") or ""),
        detail="Approval recorded — file writes remain disabled (FIX 125C)",
    )
    proposal = append_proposal_event(proposal, action="patch_proposal_approved")
    append_plan_event(plan, action="patch_proposal_approved")
    return PatchProposalResult(
        ok=True,
        proposal=proposal,
        detail="Patch proposal approved. Use FIX 125D `apply approved patch to workspace` to write (workspace only).",
    )
