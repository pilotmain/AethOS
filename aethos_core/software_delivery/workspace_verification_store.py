# SPDX-License-Identifier: Apache-2.0
"""FIX 125E — workspace verification durable state."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from aethos_core.software_delivery.workspace_verification_contract import (
    ARBITRARY_SHELL_ENABLED_FIX_125E,
    DEPENDENCY_INSTALL_ENABLED_FIX_125E,
    DEPLOY_ENABLED_FIX_125E,
    GIT_COMMIT_ENABLED_FIX_125E,
    MERGE_ENABLED_FIX_125E,
    PR_CREATION_ENABLED_FIX_125E,
    REPO_WRITE_ENABLED_FIX_125E,
    WORKSPACE_VERIFICATION_SCHEMA_VERSION,
)

_PLAN_INDEX: dict[str, str] = {}


def _store_dir() -> Path:
    root = Path(__file__).resolve().parents[2] / "data" / "software_delivery_workspace_verifications"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _path(verification_id: str) -> Path:
    safe = (verification_id or "").strip().replace("/", "_")[:128]
    return _store_dir() / f"{safe}.json"


def clear_for_tests() -> None:
    from aethos_core.software_delivery.test_data_guard import tests_may_clear_persisted_data

    if not tests_may_clear_persisted_data():
        return
    _PLAN_INDEX.clear()
    if _store_dir().exists():
        for child in _store_dir().glob("*.json"):
            child.unlink(missing_ok=True)


def load_workspace_verification(*, verification_id: str) -> dict[str, Any] | None:
    path = _path(verification_id)
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def load_workspace_verification_for_plan(*, plan_id: str) -> dict[str, Any] | None:
    vid = _PLAN_INDEX.get(plan_id)
    if vid:
        return load_workspace_verification(verification_id=vid)
    for path in _store_dir().glob("*.json"):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(payload, dict) and str(payload.get("plan_id") or "") == plan_id:
            verification_id = str(payload.get("verification_id") or "")
            if verification_id:
                _PLAN_INDEX[plan_id] = verification_id
            return payload
    return None


def save_workspace_verification(record: dict[str, Any]) -> dict[str, Any]:
    verification_id = str(record.get("verification_id") or "").strip()
    if not verification_id:
        raise ValueError("verification_id required")
    record.setdefault("schema_version", WORKSPACE_VERIFICATION_SCHEMA_VERSION)
    record["repo_write_enabled"] = REPO_WRITE_ENABLED_FIX_125E
    record["git_commit_enabled"] = GIT_COMMIT_ENABLED_FIX_125E
    record["pr_creation_enabled"] = PR_CREATION_ENABLED_FIX_125E
    record["dependency_install_enabled"] = DEPENDENCY_INSTALL_ENABLED_FIX_125E
    record["arbitrary_shell_enabled"] = ARBITRARY_SHELL_ENABLED_FIX_125E
    record["updated_at"] = datetime.now(UTC).isoformat()
    _path(verification_id).write_text(json.dumps(record, indent=2), encoding="utf-8")
    plan_id = str(record.get("plan_id") or "")
    if plan_id:
        _PLAN_INDEX[plan_id] = verification_id
    return record


def append_verification_event(
    record: dict[str, Any],
    *,
    action: str,
    detail: str = "",
    failure_class: str = "",
) -> dict[str, Any]:
    events = list(record.get("events") or [])
    events.append(
        {
            "event_id": f"sve-{uuid.uuid4().hex[:10]}",
            "action": action,
            "detail": detail,
            "failure_class": failure_class,
            "recorded_at": datetime.now(UTC).isoformat(),
            "mutation_performed": False,
        }
    )
    record["events"] = events
    return save_workspace_verification(record)


def workspace_verification_passed(*, plan_id: str) -> bool:
    record = load_workspace_verification_for_plan(plan_id=plan_id)
    if not record:
        return False
    return str(record.get("status") or "") == "passed" and bool(record.get("pr_drafting_unblocked"))
