# SPDX-License-Identifier: Apache-2.0
"""FIX 125I — governed GitHub PR open service."""

from __future__ import annotations

import os
import re
import uuid
from dataclasses import dataclass, field
from typing import Any

from aethos_core.credentials import get_provider_api_token
from aethos_core.software_delivery.branch_push_store import (
    branch_push_completed_for_plan,
    load_branch_push_for_plan,
)
from aethos_core.software_delivery.github_pr_open_contract import GITHUB_PR_OPEN_APPROVAL_PHRASE
from aethos_core.software_delivery.github_pr_open_mutation import open_governed_pull_request
from aethos_core.software_delivery.github_pr_open_receipts import record_github_pr_open_receipt
from aethos_core.software_delivery.github_pr_open_store import (
    append_pr_open_event,
    load_github_pr_open_for_plan,
    save_github_pr_open,
)
from aethos_core.software_delivery.github_pr_preflight_store import (
    github_pr_creation_approved_for_plan,
    load_github_pr_preflight_for_plan,
)
from aethos_core.software_delivery.issue_plan_store import append_plan_event, load_issue_plan_for_session
from aethos_core.software_delivery.pr_draft_store import load_pr_draft_for_plan, save_pr_draft

_OPEN_RX = re.compile(
    r"\bopen\s+(?:governed\s+)?(?:github\s+)?pull\s+request\b",
    re.I,
)
_STATUS_RX = re.compile(r"\bshow\s+governed\s+github\s+pr\s+status\b", re.I)
_REPORT_RX = re.compile(r"\bshow\s+governed\s+github\s+pr\s+report\b", re.I)


def _certification_mode() -> bool:
    return os.environ.get("AETHOS_CERTIFICATION_MODE", "").lower() in {"1", "true", "yes"}


@dataclass(frozen=True)
class GithubPrOpenResult:
    ok: bool
    record: dict[str, Any]
    detail: str = ""
    blockers: list[str] = field(default_factory=list)


def is_github_pr_open_intent(text: str) -> bool:
    raw = (text or "").strip()
    return bool(_OPEN_RX.search(raw) or _STATUS_RX.search(raw) or _REPORT_RX.search(raw))


def load_github_pr_open_config() -> dict[str, Any]:
    from aethos_core.config import get_settings

    settings = get_settings()
    return {
        "enabled": bool(getattr(settings, "software_delivery_github_pr_open_enabled", True)),
        "default_branch": str(getattr(settings, "software_delivery_github_default_branch", "main")),
    }


def _validate_pr_open_gates(
    *,
    user_text: str,
    plan: dict[str, Any],
) -> list[str]:
    blockers: list[str] = []
    plan_id = str(plan.get("plan_id") or "")

    if not branch_push_completed_for_plan(plan_id=plan_id):
        push = load_branch_push_for_plan(plan_id=plan_id)
        if not push:
            blockers.append("branch_push_missing")
        else:
            blockers.append("branch_push_not_completed")

    if not github_pr_creation_approved_for_plan(plan_id=plan_id):
        blockers.append("github_pr_preflight_not_approved")

    draft = load_pr_draft_for_plan(plan_id=plan_id)
    if not draft or str(draft.get("status") or "") != "drafted":
        blockers.append("pr_draft_missing")

    if GITHUB_PR_OPEN_APPROVAL_PHRASE not in (user_text or ""):
        blockers.append("github_pr_open_approval_required")

    return blockers


def open_governed_github_pull_request(*, session_id: str, user_text: str) -> GithubPrOpenResult:
    cfg = load_github_pr_open_config()
    if not cfg["enabled"]:
        return GithubPrOpenResult(ok=False, record={}, blockers=["github_pr_open_disabled"])

    plan = load_issue_plan_for_session(session_id=session_id)
    if not plan:
        return GithubPrOpenResult(ok=False, record={}, blockers=["issue_plan_missing"])

    plan_id = str(plan.get("plan_id") or "")
    preflight = load_github_pr_preflight_for_plan(plan_id=plan_id) or {}
    push = load_branch_push_for_plan(plan_id=plan_id) or {}
    draft = load_pr_draft_for_plan(plan_id=plan_id) or {}
    idempotency_key = str(preflight.get("idempotency_key") or push.get("idempotency_key") or "")

    existing = load_github_pr_open_for_plan(plan_id=plan_id)
    if existing and str(existing.get("status") or "") == "opened":
        if idempotency_key and existing.get("idempotency_key") == idempotency_key:
            return GithubPrOpenResult(
                ok=True,
                record=existing,
                detail="Pull request already opened (idempotent replay).",
            )

    blockers = _validate_pr_open_gates(user_text=user_text, plan=plan)
    if blockers:
        return GithubPrOpenResult(
            ok=False,
            record={},
            blockers=blockers,
            detail="PR open gates not satisfied.",
        )

    record_github_pr_open_receipt(plan_id=plan_id, phase="pr_open_gates_validated", detail="All gates passed")

    token = get_provider_api_token(provider="github")
    if not token and _certification_mode():
        token = "aethos-certification-sentinel"
    if not token:
        return GithubPrOpenResult(ok=False, record={}, blockers=["github_token_missing"])

    repository = str(plan.get("repository") or push.get("repository") or "")
    head_branch = str(push.get("branch_name") or draft.get("branch_name") or "")
    base_branch = str(push.get("default_branch") or cfg["default_branch"])
    title = str(draft.get("title") or "")
    body = str(draft.get("body") or "")

    opened = open_governed_pull_request(
        token=token,
        repository=repository,
        head=head_branch,
        base=base_branch,
        title=title,
        body=body,
    )
    if not opened.get("ok"):
        record_github_pr_open_receipt(
            plan_id=plan_id,
            phase="pull_request_opened",
            status="pr_open_failed",
            detail=str(opened.get("error") or "open failed"),
        )
        return GithubPrOpenResult(
            ok=False,
            record={},
            blockers=["github_pr_open_failed"],
            detail=str(opened.get("error") or "PR open failed"),
        )

    pr_url = str(opened.get("url") or "")
    pr_number = opened.get("number")
    record_github_pr_open_receipt(
        plan_id=plan_id,
        phase="pull_request_opened",
        detail=f"PR #{pr_number}",
        pr_url=pr_url,
    )

    pr_record = existing or {
        "pr_open_id": f"sdgpro-{uuid.uuid4().hex[:12]}",
        "plan_id": plan_id,
        "session_id": session_id,
        "preflight_id": str(preflight.get("preflight_id") or ""),
        "push_id": str(push.get("push_id") or ""),
        "draft_id": str(draft.get("draft_id") or ""),
        "events": [],
    }
    pr_record["status"] = "opened"
    pr_record["repository"] = repository
    pr_record["head_branch"] = head_branch
    pr_record["base_branch"] = base_branch
    pr_record["title"] = title
    pr_record["pr_url"] = pr_url
    pr_record["pr_number"] = pr_number
    pr_record["idempotency_key"] = idempotency_key
    pr_record["idempotent_replay"] = bool(opened.get("idempotent") or opened.get("already_exists"))
    pr_record = save_github_pr_open(pr_record)
    pr_record = append_pr_open_event(pr_record, action="pr_opened", detail=pr_url)
    record_github_pr_open_receipt(
        plan_id=plan_id,
        phase="pr_url_persisted",
        pr_open_id=str(pr_record.get("pr_open_id") or ""),
        pr_url=pr_url,
    )
    record_github_pr_open_receipt(
        plan_id=plan_id,
        phase="pr_open_completed",
        pr_open_id=str(pr_record.get("pr_open_id") or ""),
        pr_url=pr_url,
    )
    pr_record = append_pr_open_event(pr_record, action="pr_open_completed", detail=str(pr_number))

    draft["github_pr_created"] = True
    draft["github_pr_url"] = pr_url
    draft["github_pr_number"] = pr_number
    save_pr_draft(draft)

    append_plan_event(plan, action="github_pr_opened", detail=pr_url)

    detail = f"Opened PR #{pr_number} for human review."
    if pr_record.get("idempotent_replay"):
        detail = f"Pull request already exists — idempotent replay (PR #{pr_number})."

    return GithubPrOpenResult(ok=True, record=pr_record, detail=detail)


def show_github_pr_open(*, session_id: str) -> GithubPrOpenResult:
    plan = load_issue_plan_for_session(session_id=session_id)
    if not plan:
        return GithubPrOpenResult(ok=False, record={}, blockers=["issue_plan_missing"])
    record = load_github_pr_open_for_plan(plan_id=str(plan.get("plan_id") or ""))
    if not record:
        return GithubPrOpenResult(
            ok=False,
            record={},
            blockers=["github_pr_open_missing"],
            detail="Run `open governed github pull request` after branch push (125H).",
        )
    return GithubPrOpenResult(ok=True, record=record)
