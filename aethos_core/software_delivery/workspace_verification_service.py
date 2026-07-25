# SPDX-License-Identifier: Apache-2.0
"""FIX 125E — governed workspace verification service."""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from typing import Any

from aethos_core.software_delivery.issue_plan_store import (
    append_plan_event,
    load_issue_plan_for_session,
)
from aethos_core.software_delivery.patch_proposal_store import load_patch_proposal_for_plan
from aethos_core.software_delivery.workspace_application_store import (
    load_workspace_application_for_plan,
)
from aethos_core.software_delivery.workspace_verification_executor import (
    run_workspace_verification_checks,
)
from aethos_core.software_delivery.workspace_verification_receipts import (
    record_verification_receipt,
)
from aethos_core.software_delivery.workspace_verification_store import (
    append_verification_event,
    load_workspace_verification_for_plan,
    save_workspace_verification,
    workspace_verification_passed,
)

_RUN_RX = re.compile(r"\brun\s+workspace\s+verification\b", re.I)
_STATUS_RX = re.compile(r"\bshow\s+workspace\s+verification\s+status\b", re.I)
_REPORT_RX = re.compile(r"\bshow\s+workspace\s+verification\s+report\b", re.I)


@dataclass(frozen=True)
class WorkspaceVerificationResult:
    ok: bool
    verification: dict[str, Any]
    detail: str = ""
    blockers: list[str] = field(default_factory=list)


def is_workspace_verification_intent(text: str) -> bool:
    raw = (text or "").strip()
    return bool(_RUN_RX.search(raw) or _STATUS_RX.search(raw) or _REPORT_RX.search(raw))


def load_workspace_verification_config() -> dict[str, Any]:
    from aethos_core.config import get_settings

    settings = get_settings()
    return {
        "enabled": bool(getattr(settings, "software_delivery_workspace_verification_enabled", True)),
        "require_workspace_applied": bool(
            getattr(settings, "software_delivery_workspace_verification_require_applied", True)
        ),
        "allow_allowlisted_test": bool(
            getattr(settings, "software_delivery_workspace_allow_allowlisted_test", False)
        ),
    }


def pr_drafting_blocked_for_session(*, session_id: str) -> tuple[bool, list[str]]:
    """Gate for FIX 125F PR drafting — verification must exist and pass."""
    from aethos_core.software_delivery.workspace_verification_contract import (
        PR_DRAFTING_REQUIRES_VERIFICATION_FIX_125E,
    )

    if not PR_DRAFTING_REQUIRES_VERIFICATION_FIX_125E:
        return False, []
    plan = load_issue_plan_for_session(session_id=session_id)
    if not plan:
        return True, ["issue_plan_missing"]
    plan_id = str(plan.get("plan_id") or "")
    if workspace_verification_passed(plan_id=plan_id):
        return False, []
    record = load_workspace_verification_for_plan(plan_id=plan_id)
    if not record:
        return True, ["workspace_verification_missing"]
    return True, ["workspace_verification_not_passed"]


def run_workspace_verification(*, session_id: str) -> WorkspaceVerificationResult:
    cfg = load_workspace_verification_config()
    if not cfg["enabled"]:
        return WorkspaceVerificationResult(
            ok=False, verification={}, blockers=["workspace_verification_disabled"]
        )

    plan = load_issue_plan_for_session(session_id=session_id)
    if not plan:
        return WorkspaceVerificationResult(ok=False, verification={}, blockers=["issue_plan_missing"])

    plan_id = str(plan.get("plan_id") or "")
    application = load_workspace_application_for_plan(plan_id=plan_id)
    if cfg["require_workspace_applied"]:
        if not application or str(application.get("status") or "") != "applied":
            return WorkspaceVerificationResult(
                ok=False,
                verification={},
                blockers=["workspace_not_applied"],
                detail="Apply approved patch to workspace (FIX 125D) before verification.",
            )

    existing = load_workspace_verification_for_plan(plan_id=plan_id)
    if existing and str(existing.get("status") or "") == "passed":
        return WorkspaceVerificationResult(
            ok=True,
            verification=existing,
            detail="Workspace verification already passed (idempotent).",
        )

    files_applied = list(application.get("files_applied") or []) if application else []
    proposal = load_patch_proposal_for_plan(plan_id=plan_id)
    proposal_diffs = list((proposal or {}).get("unified_diffs") or [])

    record_verification_receipt(
        plan_id=plan_id,
        phase="workspace_tree_inspected",
        check_name="workspace_tree_inspected",
    )

    result = run_workspace_verification_checks(
        plan_id=plan_id,
        files_applied=files_applied,
        proposal_diffs=proposal_diffs,
        allow_allowlisted_test=cfg["allow_allowlisted_test"],
    )
    checks = list(result.get("checks") or [])
    classification = dict(result.get("classification") or {})

    phase_map = {
        "file_existence": "file_existence_verified",
        "static_diff_validation": "static_diff_validated",
        "workspace_files_modified": "static_diff_validated",
        "python_syntax": "syntax_check_completed",
        "allowlisted_test": "allowlisted_test_completed",
    }
    for check in checks:
        name = str(check.get("check") or "")
        phase = phase_map.get(name, "")
        if not phase:
            continue
        record_verification_receipt(
            plan_id=plan_id,
            phase=phase,
            status="verification_step_success" if check.get("ok") or check.get("skipped") else "verification_step_failed",
            detail=str(check.get("detail") or ""),
            check_name=name,
            failure_class=str(check.get("failure_class") or ""),
        )

    record_verification_receipt(
        plan_id=plan_id,
        phase="verification_classified",
        detail=str(classification.get("summary") or ""),
        failure_class=str(classification.get("failure_class") or ""),
        status="verification_step_success" if classification.get("status") == "passed" else "verification_step_failed",
    )

    verification = existing or {
        "verification_id": f"sdwv-{uuid.uuid4().hex[:12]}",
        "plan_id": plan_id,
        "session_id": session_id,
        "application_id": str((application or {}).get("application_id") or ""),
        "events": [],
    }
    verification["checks"] = checks
    verification["classification"] = classification
    verification["status"] = str(classification.get("status") or "failed")
    verification["failure_class"] = str(classification.get("failure_class") or "")
    verification["pr_drafting_unblocked"] = bool(classification.get("pr_drafting_unblocked"))
    verification["workspace_tree"] = str(result.get("workspace_tree") or "")
    verification = save_workspace_verification(verification)
    verification = append_verification_event(
        verification,
        action="verification_completed",
        detail=str(classification.get("summary") or ""),
        failure_class=str(classification.get("failure_class") or ""),
    )

    record_verification_receipt(
        plan_id=plan_id,
        phase="verification_completed",
        detail=str(classification.get("summary") or ""),
        failure_class=str(classification.get("failure_class") or ""),
        status="verification_step_success" if verification.get("status") == "passed" else "verification_step_failed",
    )
    append_plan_event(
        plan,
        action="workspace_verification_passed" if verification.get("status") == "passed" else "workspace_verification_failed",
        detail=str(classification.get("failure_class") or "passed"),
    )

    ok = verification.get("status") == "passed"
    return WorkspaceVerificationResult(
        ok=ok,
        verification=verification,
        detail=str(classification.get("summary") or ""),
        blockers=[] if ok else ["workspace_verification_failed"],
    )


def show_workspace_verification_status(*, session_id: str) -> WorkspaceVerificationResult:
    plan = load_issue_plan_for_session(session_id=session_id)
    if not plan:
        return WorkspaceVerificationResult(ok=False, verification={}, blockers=["issue_plan_missing"])
    verification = load_workspace_verification_for_plan(plan_id=str(plan.get("plan_id") or ""))
    if not verification:
        return WorkspaceVerificationResult(
            ok=False,
            verification={},
            blockers=["workspace_verification_missing"],
            detail="Run `run workspace verification` after workspace apply.",
        )
    return WorkspaceVerificationResult(ok=True, verification=verification)
