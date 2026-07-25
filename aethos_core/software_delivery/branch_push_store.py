# SPDX-License-Identifier: Apache-2.0
"""FIX 125H — branch push durable state."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from aethos_core.software_delivery.branch_push_contract import (
    BRANCH_PUSH_SCHEMA_VERSION,
    DEPLOY_ENABLED_FIX_125H,
    DIRECT_MAIN_PUSH_ENABLED_FIX_125H,
    GITHUB_PR_CREATE_ENABLED_FIX_125H,
    MERGE_ENABLED_FIX_125H,
)

_PLAN_INDEX: dict[str, str] = {}


def _store_dir() -> Path:
    root = Path(__file__).resolve().parents[2] / "data" / "software_delivery_github_branch_pushes"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _path(push_id: str) -> Path:
    safe = (push_id or "").strip().replace("/", "_")[:128]
    return _store_dir() / f"{safe}.json"


def clear_for_tests() -> None:
    from aethos_core.software_delivery.test_data_guard import tests_may_clear_persisted_data

    if not tests_may_clear_persisted_data():
        return
    _PLAN_INDEX.clear()
    if _store_dir().exists():
        for child in _store_dir().glob("*.json"):
            child.unlink(missing_ok=True)


def load_branch_push(*, push_id: str) -> dict[str, Any] | None:
    path = _path(push_id)
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def load_branch_push_for_plan(*, plan_id: str) -> dict[str, Any] | None:
    pid = _PLAN_INDEX.get(plan_id)
    if pid:
        return load_branch_push(push_id=pid)
    for path in _store_dir().glob("*.json"):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(payload, dict) and str(payload.get("plan_id") or "") == plan_id:
            push_id = str(payload.get("push_id") or "")
            if push_id:
                _PLAN_INDEX[plan_id] = push_id
            return payload
    return None


def save_branch_push(record: dict[str, Any]) -> dict[str, Any]:
    push_id = str(record.get("push_id") or "").strip()
    if not push_id:
        raise ValueError("push_id required")
    record.setdefault("schema_version", BRANCH_PUSH_SCHEMA_VERSION)
    record["github_pr_create_enabled"] = GITHUB_PR_CREATE_ENABLED_FIX_125H
    record["merge_enabled"] = MERGE_ENABLED_FIX_125H
    record["deploy_enabled"] = DEPLOY_ENABLED_FIX_125H
    record["direct_main_push_enabled"] = DIRECT_MAIN_PUSH_ENABLED_FIX_125H
    record["updated_at"] = datetime.now(UTC).isoformat()
    _path(push_id).write_text(json.dumps(record, indent=2), encoding="utf-8")
    plan_id = str(record.get("plan_id") or "")
    if plan_id:
        _PLAN_INDEX[plan_id] = push_id
    return record


def append_push_event(
    record: dict[str, Any],
    *,
    action: str,
    detail: str = "",
) -> dict[str, Any]:
    events = list(record.get("events") or [])
    events.append(
        {
            "event_id": f"sbpe-{uuid.uuid4().hex[:10]}",
            "action": action,
            "detail": detail,
            "recorded_at": datetime.now(UTC).isoformat(),
            "github_mutation_performed": action in {"push_completed", "feature_branch_pushed"},
        }
    )
    record["events"] = events
    return save_branch_push(record)


def branch_push_completed_for_plan(*, plan_id: str) -> bool:
    record = load_branch_push_for_plan(plan_id=plan_id)
    if not record:
        return False
    return str(record.get("status") or "") == "pushed"
