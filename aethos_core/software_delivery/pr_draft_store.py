# SPDX-License-Identifier: Apache-2.0
"""FIX 125F — durable PR draft artifacts."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from aethos_core.software_delivery.pr_draft_contract import (
    DEPLOY_ENABLED_FIX_125F,
    GITHUB_PR_CREATION_ENABLED_FIX_125F,
    GIT_COMMIT_ENABLED_FIX_125F,
    GIT_PUSH_ENABLED_FIX_125F,
    MERGE_ENABLED_FIX_125F,
    PR_DRAFT_SCHEMA_VERSION,
    REPO_WRITE_ENABLED_FIX_125F,
)

_PLAN_INDEX: dict[str, str] = {}


def _store_dir() -> Path:
    root = Path(__file__).resolve().parents[2] / "data" / "software_delivery_pr_drafts"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _path(draft_id: str) -> Path:
    safe = (draft_id or "").strip().replace("/", "_")[:128]
    return _store_dir() / f"{safe}.json"


def _artifact_path(draft_id: str) -> Path:
    safe = (draft_id or "").strip().replace("/", "_")[:128]
    return _store_dir() / f"{safe}.md"


def clear_for_tests() -> None:
    from aethos_core.software_delivery.test_data_guard import tests_may_clear_persisted_data

    if not tests_may_clear_persisted_data():
        return
    _PLAN_INDEX.clear()
    if _store_dir().exists():
        for child in _store_dir().glob("*"):
            if child.is_file():
                child.unlink(missing_ok=True)


def load_pr_draft(*, draft_id: str) -> dict[str, Any] | None:
    path = _path(draft_id)
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def load_pr_draft_for_plan(*, plan_id: str) -> dict[str, Any] | None:
    did = _PLAN_INDEX.get(plan_id)
    if did:
        return load_pr_draft(draft_id=did)
    for path in _store_dir().glob("*.json"):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(payload, dict) and str(payload.get("plan_id") or "") == plan_id:
            draft_id = str(payload.get("draft_id") or "")
            if draft_id:
                _PLAN_INDEX[plan_id] = draft_id
            return payload
    return None


def save_pr_draft(draft: dict[str, Any]) -> dict[str, Any]:
    draft_id = str(draft.get("draft_id") or "").strip()
    if not draft_id:
        raise ValueError("draft_id required")
    draft.setdefault("schema_version", PR_DRAFT_SCHEMA_VERSION)
    draft["github_pr_creation_enabled"] = GITHUB_PR_CREATION_ENABLED_FIX_125F
    draft["git_push_enabled"] = GIT_PUSH_ENABLED_FIX_125F
    draft["git_commit_enabled"] = GIT_COMMIT_ENABLED_FIX_125F
    draft["merge_enabled"] = MERGE_ENABLED_FIX_125F
    draft["deploy_enabled"] = DEPLOY_ENABLED_FIX_125F
    draft["repo_write_enabled"] = REPO_WRITE_ENABLED_FIX_125F
    draft["updated_at"] = datetime.now(UTC).isoformat()
    _path(draft_id).write_text(json.dumps(draft, indent=2), encoding="utf-8")
    body = str(draft.get("body") or "")
    if body:
        _artifact_path(draft_id).write_text(body, encoding="utf-8")
    plan_id = str(draft.get("plan_id") or "")
    if plan_id:
        _PLAN_INDEX[plan_id] = draft_id
    return draft


def append_draft_event(
    draft: dict[str, Any],
    *,
    action: str,
    detail: str = "",
) -> dict[str, Any]:
    events = list(draft.get("events") or [])
    events.append(
        {
            "event_id": f"spde-{uuid.uuid4().hex[:10]}",
            "action": action,
            "detail": detail,
            "recorded_at": datetime.now(UTC).isoformat(),
            "mutation_performed": False,
        }
    )
    draft["events"] = events
    return save_pr_draft(draft)
