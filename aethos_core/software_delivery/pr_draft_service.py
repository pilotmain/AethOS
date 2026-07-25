# SPDX-License-Identifier: Apache-2.0
"""FIX 125F — governed PR draft artifact service."""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from aethos_core.software_delivery.branch_orchestration_store import load_branch_context_for_plan
from aethos_core.software_delivery.issue_plan_store import (
    append_plan_event,
    load_issue_plan_for_session,
)
from aethos_core.software_delivery.patch_proposal_store import load_patch_proposal_for_plan
from aethos_core.software_delivery.pr_draft_contract import HUMAN_REVIEW_REQUIREMENTS
from aethos_core.software_delivery.pr_draft_receipts import record_pr_draft_receipt
from aethos_core.software_delivery.pr_draft_store import (
    append_draft_event,
    load_pr_draft_for_plan,
    save_pr_draft,
)
from aethos_core.software_delivery.workspace_application_store import (
    load_workspace_application_for_plan,
)
from aethos_core.software_delivery.workspace_verification_service import (
    pr_drafting_blocked_for_session,
)
from aethos_core.software_delivery.workspace_verification_store import (
    load_workspace_verification_for_plan,
)

_CREATE_RX = re.compile(
    r"\bcreate\s+(?:software\s+delivery\s+|governed\s+)?pr\s+draft\b",
    re.I,
)
_SHOW_RX = re.compile(
    r"\bshow\s+(?:software\s+delivery\s+)?pr\s+draft(?:\s+status)?\b",
    re.I,
)


@dataclass(frozen=True)
class PrDraftResult:
    ok: bool
    draft: dict[str, Any]
    detail: str = ""
    blockers: list[str] = field(default_factory=list)


def is_pr_draft_intent(text: str) -> bool:
    raw = (text or "").strip()
    return bool(_CREATE_RX.search(raw) or _SHOW_RX.search(raw))


def load_pr_draft_config() -> dict[str, Any]:
    from aethos_core.config import get_settings

    settings = get_settings()
    return {
        "enabled": bool(getattr(settings, "software_delivery_pr_draft_enabled", True)),
        "require_verification_passed": bool(
            getattr(settings, "software_delivery_pr_draft_require_verification", True)
        ),
    }


def _verification_summary(verification: dict[str, Any]) -> dict[str, Any]:
    classification = verification.get("classification") or {}
    checks = verification.get("checks") or []
    return {
        "verification_id": verification.get("verification_id"),
        "status": verification.get("status"),
        "failure_class": verification.get("failure_class") or "",
        "summary": classification.get("summary") or "",
        "checks_passed": sum(1 for c in checks if c.get("ok") or c.get("skipped")),
        "checks_failed": sum(1 for c in checks if not c.get("ok") and not c.get("skipped")),
        "checks": [
            {
                "name": c.get("check"),
                "ok": c.get("ok"),
                "skipped": c.get("skipped"),
                "detail": c.get("detail"),
            }
            for c in checks
        ],
    }


def _build_checklist(
    *,
    plan: dict[str, Any],
    files_applied: list[str],
    verification: dict[str, Any],
) -> list[str]:
    items = [
        "[ ] Workspace verification passed (FIX 125E)",
        "[ ] Review governed workspace diff vs repository",
        "[ ] Confirm blast radius acceptable",
        f"[ ] Validate affected files ({len(files_applied)})",
    ]
    for test in plan.get("test_expectations") or []:
        items.append(f"[ ] Run: {test}")
    intent = (load_patch_proposal_for_plan(plan_id=str(plan.get("plan_id") or "")) or {}).get(
        "patch_intent"
    ) or {}
    for step in intent.get("validation_steps") or []:
        if step not in items:
            items.append(f"[ ] {step}")
    if verification.get("status") == "passed":
        items[0] = "[x] Workspace verification passed (FIX 125E)"
    return items[:16]


def compose_pr_draft_body(
    *,
    plan: dict[str, Any],
    branch: dict[str, Any],
    proposal: dict[str, Any],
    application: dict[str, Any],
    verification: dict[str, Any],
    title: str,
) -> str:
    repo = str(plan.get("repository") or "")
    issue_num = plan.get("issue_number")
    branch_name = str(branch.get("branch_name") or "")
    files = list(application.get("files_applied") or proposal.get("proposed_files") or [])
    risk = plan.get("risk_assessment") or {}
    vsummary = _verification_summary(verification)
    checklist = _build_checklist(plan=plan, files_applied=files, verification=verification)
    rollback = list(plan.get("rollback_notes") or [])
    intent = proposal.get("patch_intent") or {}
    if intent.get("rollback_strategy"):
        rollback.append(str(intent["rollback_strategy"]))

    lines = [
        f"# {title}",
        "",
        "## Linked issue",
        f"- **{repo}#{issue_num}** — {plan.get('issue_title', '')}",
        f"- Issue URL: {plan.get('issue_url', '')}",
        "",
        "## Summary",
        str((proposal.get("patch_intent") or {}).get("summary") or plan.get("issue_title") or ""),
        "",
        "## Branch (governed context)",
        f"- `{branch_name}`",
        f"- Workspace: `{application.get('workspace_tree', '')}`",
        "",
        "## Files changed (workspace apply)",
        *[f"- `{f}`" for f in files],
        "",
        "## Verification summary (FIX 125E)",
        f"- Status: **{vsummary.get('status', '')}**",
        f"- {vsummary.get('summary', '')}",
        f"- Checks passed: **{vsummary.get('checks_passed', 0)}**",
        "",
        "## Risk",
        f"- Tier: **{risk.get('risk_tier', 'unknown')}**",
        f"- Blast radius: **{plan.get('blast_radius', '')}**",
        "",
        "## Rollback",
        *[f"- {note}" for note in rollback[:6]],
        "",
        "## Human review requirements",
        *[f"- {req}" for req in HUMAN_REVIEW_REQUIREMENTS],
        "",
        "## Review checklist",
        *checklist,
        "",
        "---",
        "*Artifact-only PR draft (FIX 125F). No GitHub PR, git push, merge, or deploy performed.*",
    ]
    return "\n".join(lines)


def create_software_delivery_pr_draft(*, session_id: str) -> PrDraftResult:
    cfg = load_pr_draft_config()
    if not cfg["enabled"]:
        return PrDraftResult(ok=False, draft={}, blockers=["pr_draft_disabled"])

    blocked, blockers = pr_drafting_blocked_for_session(session_id=session_id)
    if cfg["require_verification_passed"] and blocked:
        return PrDraftResult(
            ok=False,
            draft={},
            blockers=blockers,
            detail="Workspace verification must pass before PR draft (FIX 125E).",
        )

    plan = load_issue_plan_for_session(session_id=session_id)
    if not plan:
        return PrDraftResult(ok=False, draft={}, blockers=["issue_plan_missing"])

    plan_id = str(plan.get("plan_id") or "")
    existing = load_pr_draft_for_plan(plan_id=plan_id)
    if existing and str(existing.get("status") or "") == "drafted":
        return PrDraftResult(
            ok=True,
            draft=existing,
            detail="PR draft artifact already exists (idempotent).",
        )

    verification = load_workspace_verification_for_plan(plan_id=plan_id)
    if not verification or str(verification.get("status") or "") != "passed":
        return PrDraftResult(ok=False, draft={}, blockers=["workspace_verification_not_passed"])

    proposal = load_patch_proposal_for_plan(plan_id=plan_id) or {}
    application = load_workspace_application_for_plan(plan_id=plan_id) or {}
    branch = load_branch_context_for_plan(plan_id=plan_id) or {}

    record_pr_draft_receipt(
        plan_id=plan_id,
        phase="verification_gate_passed",
        detail="Verification gate satisfied for PR draft",
    )

    issue_title = str(plan.get("issue_title") or "Software delivery implementation")
    title = f"[AethOS SD] {issue_title}"[:120]
    body = compose_pr_draft_body(
        plan=plan,
        branch=branch,
        proposal=proposal,
        application=application,
        verification=verification,
        title=title,
    )
    checklist = _build_checklist(
        plan=plan,
        files_applied=list(application.get("files_applied") or []),
        verification=verification,
    )

    draft = {
        "draft_id": f"sdpr-{uuid.uuid4().hex[:12]}",
        "plan_id": plan_id,
        "session_id": session_id,
        "verification_id": str(verification.get("verification_id") or ""),
        "proposal_id": str(proposal.get("proposal_id") or ""),
        "application_id": str(application.get("application_id") or ""),
        "branch_context_id": str(branch.get("branch_context_id") or ""),
        "status": "drafted",
        "title": title,
        "body": body,
        "checklist": checklist,
        "human_review_requirements": list(HUMAN_REVIEW_REQUIREMENTS),
        "verification_summary": _verification_summary(verification),
        "risk_notes": str((plan.get("risk_assessment") or {}).get("risk_tier") or ""),
        "rollback_notes": list(plan.get("rollback_notes") or []),
        "branch_name": str(branch.get("branch_name") or ""),
        "files": list(application.get("files_applied") or []),
        "github_pr_created": False,
        "artifact_path": "",
        "events": [],
    }
    draft = save_pr_draft(draft)
    draft["artifact_path"] = str(
        Path(__file__).resolve().parents[2]
        / "data"
        / "software_delivery_pr_drafts"
        / f"{draft['draft_id']}.md"
    )
    draft = save_pr_draft(draft)

    record_pr_draft_receipt(
        plan_id=plan_id,
        phase="pr_draft_composed",
        draft_id=str(draft.get("draft_id") or ""),
        detail=title,
    )
    record_pr_draft_receipt(
        plan_id=plan_id,
        phase="pr_draft_persisted",
        draft_id=str(draft.get("draft_id") or ""),
    )
    draft = append_draft_event(draft, action="pr_draft_created", detail=title)
    append_plan_event(plan, action="pr_draft_created", detail=str(draft.get("draft_id") or ""))

    return PrDraftResult(
        ok=True,
        draft=draft,
        detail="Governed PR draft artifact created (no GitHub PR or git mutation).",
    )


def show_pr_draft(*, session_id: str) -> PrDraftResult:
    plan = load_issue_plan_for_session(session_id=session_id)
    if not plan:
        return PrDraftResult(ok=False, draft={}, blockers=["issue_plan_missing"])
    draft = load_pr_draft_for_plan(plan_id=str(plan.get("plan_id") or ""))
    if not draft:
        return PrDraftResult(
            ok=False,
            draft={},
            blockers=["pr_draft_missing"],
            detail="Run `create software delivery pr draft` after verification passes.",
        )
    return PrDraftResult(ok=True, draft=draft)
