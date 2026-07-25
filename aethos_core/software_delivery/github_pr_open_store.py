# SPDX-License-Identifier: Apache-2.0
"""FIX 125I — GitHub PR open durable state."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from aethos_core.software_delivery.github_pr_open_contract import (
    AUTO_REVIEW_APPROVAL_ENABLED_FIX_125I,
    DEPLOY_ENABLED_FIX_125I,
    GITHUB_PR_OPEN_SCHEMA_VERSION,
    HUMAN_REVIEW_REQUIRED_FIX_125I,
    MERGE_ENABLED_FIX_125I,
    RAILWAY_MUTATION_ENABLED_FIX_125I,
)

_PLAN_INDEX: dict[str, str] = {}


def _store_dir() -> Path:
    root = Path(__file__).resolve().parents[2] / "data" / "software_delivery_github_pr_opens"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _path(pr_open_id: str) -> Path:
    safe = (pr_open_id or "").strip().replace("/", "_")[:128]
    return _store_dir() / f"{safe}.json"


def clear_for_tests() -> None:
    from aethos_core.software_delivery.test_data_guard import tests_may_clear_persisted_data

    if not tests_may_clear_persisted_data():
        return
    _PLAN_INDEX.clear()
    if _store_dir().exists():
        for child in _store_dir().glob("*.json"):
            child.unlink(missing_ok=True)


def load_github_pr_open(*, pr_open_id: str) -> dict[str, Any] | None:
    path = _path(pr_open_id)
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def load_github_pr_open_for_plan(*, plan_id: str) -> dict[str, Any] | None:
    pid = _PLAN_INDEX.get(plan_id)
    if pid:
        return load_github_pr_open(pr_open_id=pid)
    for path in _store_dir().glob("*.json"):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(payload, dict) and str(payload.get("plan_id") or "") == plan_id:
            pr_open_id = str(payload.get("pr_open_id") or "")
            if pr_open_id:
                _PLAN_INDEX[plan_id] = pr_open_id
            return payload
    return None


def save_github_pr_open(record: dict[str, Any]) -> dict[str, Any]:
    pr_open_id = str(record.get("pr_open_id") or "").strip()
    if not pr_open_id:
        raise ValueError("pr_open_id required")
    record.setdefault("schema_version", GITHUB_PR_OPEN_SCHEMA_VERSION)
    record["merge_enabled"] = MERGE_ENABLED_FIX_125I
    record["deploy_enabled"] = DEPLOY_ENABLED_FIX_125I
    record["railway_mutation_enabled"] = RAILWAY_MUTATION_ENABLED_FIX_125I
    record["auto_review_approval_enabled"] = AUTO_REVIEW_APPROVAL_ENABLED_FIX_125I
    record["human_review_required"] = HUMAN_REVIEW_REQUIRED_FIX_125I
    record["updated_at"] = datetime.now(UTC).isoformat()
    _path(pr_open_id).write_text(json.dumps(record, indent=2), encoding="utf-8")
    plan_id = str(record.get("plan_id") or "")
    if plan_id:
        _PLAN_INDEX[plan_id] = pr_open_id
    return record


def append_pr_open_event(
    record: dict[str, Any],
    *,
    action: str,
    detail: str = "",
) -> dict[str, Any]:
    events = list(record.get("events") or [])
    events.append(
        {
            "event_id": f"sgpe-{uuid.uuid4().hex[:10]}",
            "action": action,
            "detail": detail,
            "recorded_at": datetime.now(UTC).isoformat(),
            "github_pr_open_performed": action in {"pr_opened", "pr_open_completed"},
        }
    )
    record["events"] = events
    return save_github_pr_open(record)


def _pr_open_success_from_receipts(*, plan_id: str) -> bool:
    from aethos_core.software_delivery.github_pr_open_receipts import list_github_pr_open_receipts

    for receipt in list_github_pr_open_receipts(plan_id=plan_id):
        if str(receipt.get("status") or "") != "pr_open_success":
            continue
        if str(receipt.get("pr_url") or "").startswith("https://"):
            return True
        detail = str(receipt.get("detail") or "")
        if detail.startswith("PR #"):
            return True
    return False


def _pr_open_completed_local(*, plan_id: str) -> bool:
    record = load_github_pr_open_for_plan(plan_id=plan_id)
    if record and str(record.get("status") or "") == "opened":
        return True
    return _pr_open_success_from_receipts(plan_id=plan_id)


def _resolve_feature_branch_for_plan(*, plan_id: str) -> str:
    from aethos_core.software_delivery.branch_push_receipts import list_branch_push_receipts
    from aethos_core.software_delivery.github_pr_preflight_store import load_github_pr_preflight_for_plan
    from aethos_core.software_delivery.pr_draft_store import load_pr_draft_for_plan

    preflight = load_github_pr_preflight_for_plan(plan_id=plan_id)
    if preflight:
        for check in list(preflight.get("checks") or []):
            if not isinstance(check, dict):
                continue
            for key in ("feature_branch", "branch_name"):
                branch = str(check.get(key) or "")
                if branch.startswith("aethos/"):
                    return branch

    for receipt in list_branch_push_receipts(plan_id=plan_id):
        phase = str(receipt.get("phase") or "")
        detail = str(receipt.get("detail") or "")
        if phase in {"feature_branch_created", "feature_branch_pushed"} and detail.startswith("aethos/"):
            return detail

    draft = load_pr_draft_for_plan(plan_id=plan_id)
    if draft:
        branch = str(draft.get("branch_name") or "")
        if branch.startswith("aethos/"):
            return branch
        body = str(draft.get("body") or "")
        if "`" in body:
            import re

            match = re.search(r"`(aethos/[^`]+)`", body)
            if match:
                return match.group(1)

    from aethos_core.software_delivery.branch_orchestration_store import load_branch_context_for_plan

    ctx = load_branch_context_for_plan(plan_id=plan_id)
    if ctx:
        branch = str(ctx.get("branch_name") or "")
        if branch.startswith("aethos/"):
            return branch
    return ""


def _branch_head_for_plan(*, plan_id: str) -> tuple[str, str] | None:
    from aethos_core.software_delivery.branch_orchestration_store import load_branch_context_for_plan
    from aethos_core.software_delivery.issue_plan_store import load_issue_plan

    plan = load_issue_plan(plan_id=plan_id) or {}
    repository = str(plan.get("repository") or "")
    ctx = load_branch_context_for_plan(plan_id=plan_id)
    if not repository and ctx:
        repository = str(ctx.get("repository") or "")
    if not repository:
        repository = "pilotmain/AethOS"

    branch = _resolve_feature_branch_for_plan(plan_id=plan_id)
    if branch:
        return repository, branch
    return None


def _github_pr_open_verified_readonly(*, plan_id: str) -> bool:
    head = _branch_head_for_plan(plan_id=plan_id)
    if not head:
        return False
    repository, branch_name = head
    owner, _, repo = repository.partition("/")
    if not owner or not repo or not branch_name:
        return False

    from aethos_core.credentials import get_provider_api_token
    from aethos_core.providers.github.api_client import request_github
    from aethos_core.software_delivery.issue_plan_store import load_issue_plan

    token = get_provider_api_token(provider="github", require_validated=False)
    if not token:
        return False

    resp = request_github(
        token,
        "GET",
        f"/repos/{owner}/{repo}/pulls",
        params={"head": f"{owner}:{branch_name}", "state": "all", "per_page": 5},
    )
    if not resp.get("ok"):
        return False
    pulls = resp.get("data") or []
    if not isinstance(pulls, list) or not pulls:
        return False
    first = pulls[0] if isinstance(pulls[0], dict) else {}
    if not first.get("number"):
        return False
    plan = load_issue_plan(plan_id=plan_id) or {}
    save_github_pr_open(
        {
            "pr_open_id": f"sdgpro-{uuid.uuid4().hex[:12]}",
            "plan_id": plan_id,
            "session_id": str(plan.get("session_id") or "operator"),
            "status": "opened",
            "repository": repository,
            "head_branch": branch_name,
            "base_branch": str(first.get("base", {}).get("ref") or "main"),
            "title": str(first.get("title") or ""),
            "pr_url": str(first.get("html_url") or ""),
            "pr_number": int(first.get("number") or 0),
            "recovered_from_github_readonly": True,
            "events": [],
        }
    )
    return True


def github_pr_open_completed_for_plan(*, plan_id: str, verify_github: bool = False) -> bool:
    if _pr_open_completed_local(plan_id=plan_id):
        return True
    if verify_github:
        return _github_pr_open_verified_readonly(plan_id=plan_id)
    return False
