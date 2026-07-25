# SPDX-License-Identifier: Apache-2.0
"""FIX 125B — branch context store (one issue plan → one branch context)."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from aethos_core.software_delivery.branch_orchestration_contract import (
    BRANCH_ORCHESTRATION_SCHEMA_VERSION,
    CODE_MODIFICATION_ENABLED_FIX_125B,
    MERGE_ENABLED_FIX_125B,
    PR_CREATION_ENABLED_FIX_125B,
)

_PLAN_INDEX: dict[str, str] = {}


def _store_dir() -> Path:
    root = Path(__file__).resolve().parents[2] / "data" / "software_delivery_branch_contexts"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _workspace_root() -> Path:
    root = Path(__file__).resolve().parents[2] / "data" / "software_delivery_workspaces"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _path(branch_context_id: str) -> Path:
    safe = (branch_context_id or "").strip().replace("/", "_")[:128]
    return _store_dir() / f"{safe}.json"


def clear_for_tests() -> None:
    from aethos_core.software_delivery.test_data_guard import tests_may_clear_persisted_data

    if not tests_may_clear_persisted_data():
        return
    _PLAN_INDEX.clear()
    if _store_dir().exists():
        for child in _store_dir().glob("*.json"):
            child.unlink(missing_ok=True)
    if _workspace_root().exists():
        for child in _workspace_root().iterdir():
            if child.is_dir():
                import shutil

                shutil.rmtree(child, ignore_errors=True)


def load_branch_context(*, branch_context_id: str) -> dict[str, Any] | None:
    path = _path(branch_context_id)
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def load_branch_context_for_plan(*, plan_id: str) -> dict[str, Any] | None:
    ctx_id = _PLAN_INDEX.get(plan_id)
    if ctx_id:
        return load_branch_context(branch_context_id=ctx_id)
    for path in _store_dir().glob("*.json"):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(payload, dict) and str(payload.get("plan_id") or "") == plan_id:
            bid = str(payload.get("branch_context_id") or "")
            if bid:
                _PLAN_INDEX[plan_id] = bid
            return payload
    return None


def workspace_path_for_plan(*, plan_id: str) -> Path:
    safe = (plan_id or "").strip().replace("/", "_")[:128]
    path = _workspace_root() / safe
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_branch_context(ctx: dict[str, Any]) -> dict[str, Any]:
    ctx_id = str(ctx.get("branch_context_id") or "").strip()
    if not ctx_id:
        raise ValueError("branch_context_id required")
    ctx.setdefault("schema_version", BRANCH_ORCHESTRATION_SCHEMA_VERSION)
    ctx["code_modification_enabled"] = CODE_MODIFICATION_ENABLED_FIX_125B
    ctx["pr_creation_enabled"] = PR_CREATION_ENABLED_FIX_125B
    ctx["merge_enabled"] = MERGE_ENABLED_FIX_125B
    ctx["updated_at"] = datetime.now(UTC).isoformat()
    _path(ctx_id).write_text(json.dumps(ctx, indent=2), encoding="utf-8")
    plan_id = str(ctx.get("plan_id") or "")
    if plan_id:
        _PLAN_INDEX[plan_id] = ctx_id
    return ctx


def append_branch_event(
    ctx: dict[str, Any],
    *,
    action: str,
    actor: str = "operator",
    detail: str = "",
) -> dict[str, Any]:
    events = list(ctx.get("events") or [])
    events.append(
        {
            "event_id": f"sbe-{uuid.uuid4().hex[:10]}",
            "action": action,
            "actor": actor,
            "detail": detail,
            "recorded_at": datetime.now(UTC).isoformat(),
            "mutation_performed": False,
        }
    )
    ctx["events"] = events
    return save_branch_context(ctx)
