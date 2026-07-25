# SPDX-License-Identifier: Apache-2.0
"""FIX 125G — GitHub PR preflight durable state."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from aethos_core.software_delivery.github_pr_preflight_contract import (
    DEPLOY_ENABLED_FIX_125G,
    GITHUB_PR_CREATE_ENABLED_FIX_125G,
    GIT_PUSH_ENABLED_FIX_125G,
    GITHUB_PR_PREFLIGHT_SCHEMA_VERSION,
    MERGE_ENABLED_FIX_125G,
    REPO_WRITE_ENABLED_FIX_125G,
)

_PLAN_INDEX: dict[str, str] = {}


def _store_dir() -> Path:
    root = Path(__file__).resolve().parents[2] / "data" / "software_delivery_github_pr_preflights"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _path(preflight_id: str) -> Path:
    safe = (preflight_id or "").strip().replace("/", "_")[:128]
    return _store_dir() / f"{safe}.json"


def clear_for_tests() -> None:
    from aethos_core.software_delivery.test_data_guard import tests_may_clear_persisted_data

    if not tests_may_clear_persisted_data():
        return
    _PLAN_INDEX.clear()
    if _store_dir().exists():
        for child in _store_dir().glob("*.json"):
            child.unlink(missing_ok=True)


def load_github_pr_preflight(*, preflight_id: str) -> dict[str, Any] | None:
    path = _path(preflight_id)
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def load_github_pr_preflight_for_plan(*, plan_id: str) -> dict[str, Any] | None:
    pid = _PLAN_INDEX.get(plan_id)
    if pid:
        return load_github_pr_preflight(preflight_id=pid)
    for path in _store_dir().glob("*.json"):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(payload, dict) and str(payload.get("plan_id") or "") == plan_id:
            preflight_id = str(payload.get("preflight_id") or "")
            if preflight_id:
                _PLAN_INDEX[plan_id] = preflight_id
            return payload
    return None


def save_github_pr_preflight(record: dict[str, Any]) -> dict[str, Any]:
    preflight_id = str(record.get("preflight_id") or "").strip()
    if not preflight_id:
        raise ValueError("preflight_id required")
    record.setdefault("schema_version", GITHUB_PR_PREFLIGHT_SCHEMA_VERSION)
    record["git_push_enabled"] = GIT_PUSH_ENABLED_FIX_125G
    record["github_pr_create_enabled"] = GITHUB_PR_CREATE_ENABLED_FIX_125G
    record["repo_write_enabled"] = REPO_WRITE_ENABLED_FIX_125G
    record["merge_enabled"] = MERGE_ENABLED_FIX_125G
    record["deploy_enabled"] = DEPLOY_ENABLED_FIX_125G
    record["updated_at"] = datetime.now(UTC).isoformat()
    _path(preflight_id).write_text(json.dumps(record, indent=2), encoding="utf-8")
    plan_id = str(record.get("plan_id") or "")
    if plan_id:
        _PLAN_INDEX[plan_id] = preflight_id
    return record


def append_preflight_event(
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
            "github_mutation_performed": False,
        }
    )
    record["events"] = events
    return save_github_pr_preflight(record)


def github_pr_creation_approved_for_plan(*, plan_id: str) -> bool:
    record = load_github_pr_preflight_for_plan(plan_id=plan_id)
    if not record:
        return False
    return (
        str(record.get("status") or "") == "preflight_passed"
        and bool(record.get("preflight_approved"))
        and bool(record.get("github_creation_unblocked"))
    )
