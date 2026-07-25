# SPDX-License-Identifier: Apache-2.0
"""FIX 125G — GitHub PR creation preflight service."""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from typing import Any

from aethos_core.software_delivery.branch_orchestration_store import load_branch_context_for_plan
from aethos_core.software_delivery.github_pr_preflight_contract import (
    GITHUB_PR_PREFLIGHT_APPROVAL_PHRASE,
)
from aethos_core.software_delivery.github_pr_preflight_executor import run_github_pr_preflight_checks
from aethos_core.software_delivery.github_pr_preflight_receipts import record_github_pr_preflight_receipt
from aethos_core.software_delivery.github_pr_preflight_store import (
    append_preflight_event,
    github_pr_creation_approved_for_plan,
    load_github_pr_preflight_for_plan,
    save_github_pr_preflight,
)
from aethos_core.software_delivery.issue_plan_store import (
    append_plan_event,
    load_issue_plan_for_session,
)
from aethos_core.software_delivery.pr_draft_store import load_pr_draft_for_plan
from aethos_core.software_delivery.workspace_application_store import load_workspace_application_for_plan
from aethos_core.software_delivery.workspace_verification_store import load_workspace_verification_for_plan

_RUN_RX = re.compile(r"\brun\s+github\s+pr\s+creation\s+preflight\b", re.I)
_STATUS_RX = re.compile(r"\bshow\s+github\s+pr\s+creation\s+preflight(?:\s+status)?\b", re.I)
_REPORT_RX = re.compile(r"\bshow\s+github\s+pr\s+creation\s+preflight\s+report\b", re.I)
_APPROVE_RX = re.compile(r"\bapprove\s+github\s+pr\s+creation\s+preflight\b", re.I)


@dataclass(frozen=True)
class GithubPrPreflightResult:
    ok: bool
    preflight: dict[str, Any]
    detail: str = ""
    blockers: list[str] = field(default_factory=list)


def is_github_pr_preflight_intent(text: str) -> bool:
    raw = (text or "").strip()
    return bool(
        _RUN_RX.search(raw) or _STATUS_RX.search(raw) or _REPORT_RX.search(raw) or _APPROVE_RX.search(raw)
    )


def load_github_pr_preflight_config() -> dict[str, Any]:
    from aethos_core.config import get_settings

    settings = get_settings()
    return {
        "enabled": bool(getattr(settings, "software_delivery_github_pr_preflight_enabled", True)),
        "require_pr_draft": bool(getattr(settings, "software_delivery_github_pr_preflight_require_draft", True)),
    }


def github_pr_creation_blocked_for_session(*, session_id: str) -> tuple[bool, list[str]]:
    plan = load_issue_plan_for_session(session_id=session_id)
    if not plan:
        return True, ["issue_plan_missing"]
    if github_pr_creation_approved_for_plan(plan_id=str(plan.get("plan_id") or "")):
        return False, []
    record = load_github_pr_preflight_for_plan(plan_id=str(plan.get("plan_id") or ""))
    if not record:
        return True, ["github_pr_preflight_missing"]
    if str(record.get("status") or "") != "preflight_passed":
        return True, ["github_pr_preflight_not_passed"]
    return True, ["github_pr_preflight_not_approved"]


def run_github_pr_creation_preflight(*, session_id: str) -> GithubPrPreflightResult:
    cfg = load_github_pr_preflight_config()
    if not cfg["enabled"]:
        return GithubPrPreflightResult(ok=False, preflight={}, blockers=["github_pr_preflight_disabled"])

    plan = load_issue_plan_for_session(session_id=session_id)
    if not plan:
        return GithubPrPreflightResult(ok=False, preflight={}, blockers=["issue_plan_missing"])

    plan_id = str(plan.get("plan_id") or "")
    draft = load_pr_draft_for_plan(plan_id=plan_id)
    if cfg["require_pr_draft"] and not draft:
        return GithubPrPreflightResult(
            ok=False,
            preflight={},
            blockers=["pr_draft_missing"],
            detail="Create PR draft (125F) before GitHub preflight.",
        )

    existing = load_github_pr_preflight_for_plan(plan_id=plan_id)
    if existing and str(existing.get("status") or "") == "preflight_passed":
        return GithubPrPreflightResult(
            ok=True,
            preflight=existing,
            detail="Preflight already passed (idempotent).",
        )

    verification = load_workspace_verification_for_plan(plan_id=plan_id) or {}
    application = load_workspace_application_for_plan(plan_id=plan_id) or {}
    branch = load_branch_context_for_plan(plan_id=plan_id) or {}

    result = run_github_pr_preflight_checks(
        plan=plan,
        draft=draft or {},
        branch=branch,
        application=application,
        verification=verification,
    )

    phase_map = {
        "pr_creation_readiness_gate": "readiness_gate_evaluated",
        "github_auth_scope": "github_auth_scope_checked",
        "branch_push_readiness": "branch_push_readiness_assessed",
        "diff_package_size": "diff_package_measured",
        "protected_branch_policy": "protected_branch_policy_reviewed",
        "mutation_preview": "mutation_preview_recorded",
        "pr_title_body_review": "readiness_gate_evaluated",
    }
    for check in result.get("checks") or []:
        name = str(check.get("check") or "")
        phase = phase_map.get(name)
        if phase:
            record_github_pr_preflight_receipt(
                plan_id=plan_id,
                phase=phase,
                detail=str(check.get("detail") or ""),
                status="preflight_step_success" if check.get("ok") else "preflight_step_failed",
            )

    classification = dict(result.get("classification") or {})
    preflight = existing or {
        "preflight_id": f"sdgpf-{uuid.uuid4().hex[:12]}",
        "plan_id": plan_id,
        "session_id": session_id,
        "draft_id": str((draft or {}).get("draft_id") or ""),
        "events": [],
    }
    preflight["checks"] = list(result.get("checks") or [])
    preflight["classification"] = classification
    preflight["status"] = str(classification.get("status") or "preflight_failed")
    preflight["failure_class"] = str(classification.get("failure_class") or "")
    preflight["idempotency_key"] = str(result.get("idempotency_key") or "")
    preflight["mutation_preview"] = result.get("mutation_preview") or {}
    preflight["rollback_cleanup_plan"] = result.get("rollback_cleanup_plan") or {}
    preflight["pr_final_review"] = result.get("pr_final_review") or {}
    preflight["preflight_approved"] = False
    preflight["github_creation_unblocked"] = False
    preflight = save_github_pr_preflight(preflight)
    preflight = append_preflight_event(
        preflight,
        action="preflight_completed",
        detail=str(classification.get("summary") or ""),
    )
    record_github_pr_preflight_receipt(
        plan_id=plan_id,
        phase="preflight_completed",
        preflight_id=str(preflight.get("preflight_id") or ""),
        detail=str(classification.get("summary") or ""),
        status="preflight_step_success" if preflight.get("status") == "preflight_passed" else "preflight_step_failed",
    )
    append_plan_event(
        plan,
        action="github_pr_preflight_passed" if preflight.get("status") == "preflight_passed" else "github_pr_preflight_failed",
    )

    ok = preflight.get("status") == "preflight_passed"
    return GithubPrPreflightResult(
        ok=ok,
        preflight=preflight,
        detail=str(classification.get("summary") or ""),
        blockers=[] if ok else ["github_pr_preflight_failed"],
    )


def approve_github_pr_creation_preflight(
    *,
    session_id: str,
    user_text: str,
) -> GithubPrPreflightResult:
    plan = load_issue_plan_for_session(session_id=session_id)
    if not plan:
        return GithubPrPreflightResult(ok=False, preflight={}, blockers=["issue_plan_missing"])

    preflight = load_github_pr_preflight_for_plan(plan_id=str(plan.get("plan_id") or ""))
    if not preflight:
        return GithubPrPreflightResult(
            ok=False,
            preflight={},
            blockers=["github_pr_preflight_missing"],
            detail="Run `run github pr creation preflight` first.",
        )

    if str(preflight.get("status") or "") != "preflight_passed":
        return GithubPrPreflightResult(
            ok=False,
            preflight=preflight,
            blockers=["github_pr_preflight_not_passed"],
        )

    if GITHUB_PR_PREFLIGHT_APPROVAL_PHRASE not in (user_text or ""):
        return GithubPrPreflightResult(
            ok=False,
            preflight=preflight,
            blockers=["github_pr_preflight_approval_required"],
            detail=f"Phrase required: {GITHUB_PR_PREFLIGHT_APPROVAL_PHRASE}",
        )

    if preflight.get("preflight_approved"):
        return GithubPrPreflightResult(
            ok=True,
            preflight=preflight,
            detail="Preflight already approved (idempotent).",
        )

    preflight["preflight_approved"] = True
    preflight["github_creation_unblocked"] = True
    preflight = save_github_pr_preflight(preflight)
    preflight = append_preflight_event(preflight, action="preflight_approved")
    record_github_pr_preflight_receipt(
        plan_id=str(plan.get("plan_id") or ""),
        phase="preflight_approved",
        preflight_id=str(preflight.get("preflight_id") or ""),
    )
    append_plan_event(plan, action="github_pr_preflight_approved")
    return GithubPrPreflightResult(
        ok=True,
        preflight=preflight,
        detail="Preflight approved. GitHub push/PR still require FIX 125H/125I.",
    )


def show_github_pr_preflight(*, session_id: str) -> GithubPrPreflightResult:
    plan = load_issue_plan_for_session(session_id=session_id)
    if not plan:
        return GithubPrPreflightResult(ok=False, preflight={}, blockers=["issue_plan_missing"])
    preflight = load_github_pr_preflight_for_plan(plan_id=str(plan.get("plan_id") or ""))
    if not preflight:
        return GithubPrPreflightResult(
            ok=False,
            preflight={},
            blockers=["github_pr_preflight_missing"],
        )
    return GithubPrPreflightResult(ok=True, preflight=preflight)
