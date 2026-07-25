# SPDX-License-Identifier: Apache-2.0
"""FIX 125D — workspace application durable state."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from aethos_core.software_delivery.workspace_application_contract import (
    DEPENDENCY_INSTALL_ENABLED_FIX_125D,
    DEPLOY_ENABLED_FIX_125D,
    GIT_COMMIT_ENABLED_FIX_125D,
    INFRA_MUTATION_ENABLED_FIX_125D,
    MERGE_ENABLED_FIX_125D,
    PR_CREATION_ENABLED_FIX_125D,
    REPO_WRITE_ENABLED_FIX_125D,
    SHELL_EXECUTION_ENABLED_FIX_125D,
    WORKSPACE_APPLICATION_SCHEMA_VERSION,
)

_PLAN_INDEX: dict[str, str] = {}


def _store_dir() -> Path:
    root = Path(__file__).resolve().parents[2] / "data" / "software_delivery_workspace_applications"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _path(application_id: str) -> Path:
    safe = (application_id or "").strip().replace("/", "_")[:128]
    return _store_dir() / f"{safe}.json"


def clear_for_tests() -> None:
    from aethos_core.software_delivery.test_data_guard import tests_may_clear_persisted_data

    if not tests_may_clear_persisted_data():
        return
    _PLAN_INDEX.clear()
    if _store_dir().exists():
        for child in _store_dir().glob("*.json"):
            child.unlink(missing_ok=True)


def load_workspace_application(*, application_id: str) -> dict[str, Any] | None:
    path = _path(application_id)
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def load_workspace_application_for_plan(*, plan_id: str) -> dict[str, Any] | None:
    app_id = _PLAN_INDEX.get(plan_id)
    if app_id:
        return load_workspace_application(application_id=app_id)
    for path in _store_dir().glob("*.json"):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(payload, dict) and str(payload.get("plan_id") or "") == plan_id:
            aid = str(payload.get("application_id") or "")
            if aid:
                _PLAN_INDEX[plan_id] = aid
            return payload
    return None


def save_workspace_application(record: dict[str, Any]) -> dict[str, Any]:
    app_id = str(record.get("application_id") or "").strip()
    if not app_id:
        raise ValueError("application_id required")
    record.setdefault("schema_version", WORKSPACE_APPLICATION_SCHEMA_VERSION)
    record["repo_write_enabled"] = REPO_WRITE_ENABLED_FIX_125D
    record["git_commit_enabled"] = GIT_COMMIT_ENABLED_FIX_125D
    record["pr_creation_enabled"] = PR_CREATION_ENABLED_FIX_125D
    record["merge_enabled"] = MERGE_ENABLED_FIX_125D
    record["deploy_enabled"] = DEPLOY_ENABLED_FIX_125D
    record["infra_mutation_enabled"] = INFRA_MUTATION_ENABLED_FIX_125D
    record["shell_execution_enabled"] = SHELL_EXECUTION_ENABLED_FIX_125D
    record["dependency_install_enabled"] = DEPENDENCY_INSTALL_ENABLED_FIX_125D
    record["updated_at"] = datetime.now(UTC).isoformat()
    _path(app_id).write_text(json.dumps(record, indent=2), encoding="utf-8")
    plan_id = str(record.get("plan_id") or "")
    if plan_id:
        _PLAN_INDEX[plan_id] = app_id
    return record


def append_apply_event(
    record: dict[str, Any],
    *,
    action: str,
    actor: str = "operator",
    detail: str = "",
    files: list[str] | None = None,
) -> dict[str, Any]:
    events = list(record.get("events") or [])
    events.append(
        {
            "event_id": f"swe-{uuid.uuid4().hex[:10]}",
            "action": action,
            "actor": actor,
            "detail": detail,
            "files": list(files or []),
            "recorded_at": datetime.now(UTC).isoformat(),
            "repo_write_performed": False,
            "workspace_write_performed": action
            in {
                "patch_applied_to_workspace",
                "workspace_apply_completed",
                "workspace_rollback_completed",
            },
        }
    )
    record["events"] = events
    return save_workspace_application(record)
