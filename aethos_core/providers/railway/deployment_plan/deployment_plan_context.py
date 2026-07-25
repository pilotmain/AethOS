# SPDX-License-Identifier: Apache-2.0
"""Durable Railway new-service deployment plan context."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from aethos_core.providers.railway.deployment_plan.deployment_plan_global_index import (
    clear_global_index_for_tests,
    load_latest_active_plan,
    load_newest_plan_from_files,
    load_plan_by_repo,
    load_plan_from_route_trace,
    register_plan_in_global_index,
)

_CONTEXT_STORE: dict[str, dict[str, Any]] = {}


def _store_dir() -> Path:
    root = Path(__file__).resolve().parents[3] / "data" / "railway_deployment_plan"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _session_path(session_id: str) -> Path:
    safe = (session_id or "default").strip().replace("/", "_")[:128]
    return _store_dir() / f"{safe}_plan.json"


def save_deployment_plan_context(
    *,
    session_id: str,
    plan: dict[str, Any],
    skip_lifecycle_sync: bool = False,
) -> None:
    session_id = (session_id or "default").strip()
    payload = dict(plan)
    payload["updated_at"] = datetime.now(UTC).isoformat()
    plan_id = register_plan_in_global_index(session_id=session_id, plan=payload, plan_id=str(payload.get("plan_id") or ""))
    if plan_id:
        payload["plan_id"] = plan_id
    _CONTEXT_STORE[session_id] = payload
    try:
        _session_path(session_id).write_text(json.dumps(payload, indent=2), encoding="utf-8")
    except OSError:
        pass
    if not skip_lifecycle_sync and payload.get("repo"):
        from aethos_core.providers.railway.deployment_lifecycle.deployment_lifecycle_sync import (
            sync_lifecycle_after_plan,
        )

        sync_lifecycle_after_plan(session_id=session_id, plan=payload)


def get_deployment_plan_context(*, session_id: str) -> dict[str, Any] | None:
    session_id = (session_id or "default").strip()
    cached = _CONTEXT_STORE.get(session_id)
    if cached is not None:
        return dict(cached)
    path = _session_path(session_id)
    if path.is_file():
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(raw, dict) and raw.get("repo"):
                _CONTEXT_STORE[session_id] = raw
                return dict(raw)
        except (OSError, json.JSONDecodeError):
            pass
    return None


def resolve_deployment_plan_context(*, session_id: str, user_text: str = "") -> dict[str, Any] | None:
    """Hydrate plan: session file → repo hint → latest global → route trace."""
    session_id = (session_id or "default").strip()
    plan = get_deployment_plan_context(session_id=session_id)
    if plan and plan.get("repo"):
        return plan

    from aethos_core.providers.railway.deployment_readiness.deployment_readiness_checks import (
        extract_github_repo_target,
    )

    repo_hint = extract_github_repo_target(user_text or "")
    if repo_hint:
        plan = load_plan_by_repo(repo_hint)
        if plan:
            _CONTEXT_STORE[session_id] = plan
            return dict(plan)

    plan = load_latest_active_plan()
    if plan:
        _CONTEXT_STORE[session_id] = plan
        return dict(plan)

    plan = load_plan_from_route_trace(session_id=session_id)
    if plan:
        _CONTEXT_STORE[session_id] = plan
        return dict(plan)

    plan = load_newest_plan_from_files()
    if plan:
        _CONTEXT_STORE[session_id] = plan
        return dict(plan)

    return None


def clear_deployment_plan_context(*, session_id: str | None = None) -> None:
    if session_id:
        sid = session_id.strip()
        _CONTEXT_STORE.pop(sid, None)
        try:
            _session_path(sid).unlink(missing_ok=True)
        except OSError:
            pass
        return
    _CONTEXT_STORE.clear()


def clear_for_tests() -> None:
    clear_deployment_plan_context()
    clear_global_index_for_tests()
    root = _store_dir()
    for path in root.glob("*.json"):
        path.unlink()
