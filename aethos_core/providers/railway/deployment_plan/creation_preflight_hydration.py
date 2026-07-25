# SPDX-License-Identifier: Apache-2.0
"""Resolve durable service creation preflight across sessions."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _store_dir() -> Path:
    root = Path(__file__).resolve().parents[3] / "data" / "railway_deployment_creation_preflight"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _load_preflight_file(path: Path) -> dict[str, Any] | None:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if isinstance(raw, dict) and raw.get("preflight_id"):
        return dict(raw)
    return None


def load_preflight_by_plan_id(plan_id: str) -> dict[str, Any] | None:
    target = (plan_id or "").strip()
    if not target:
        return None
    newest: dict[str, Any] | None = None
    newest_key = ""
    for path in _store_dir().glob("*_preflight.json"):
        row = _load_preflight_file(path)
        if not row:
            continue
        if str(row.get("plan_id") or "") != target:
            continue
        sort_key = str(row.get("updated_at") or path.stat().st_mtime)
        if sort_key >= newest_key:
            newest_key = sort_key
            newest = row
    return newest


def load_preflight_by_repo(repo: str) -> dict[str, Any] | None:
    target = (repo or "").strip().lower()
    if not target:
        return None
    newest: dict[str, Any] | None = None
    newest_key = ""
    for path in _store_dir().glob("*_preflight.json"):
        row = _load_preflight_file(path)
        if not row:
            continue
        row_repo = str(row.get("repo") or "").lower()
        snapshot_repo = str((row.get("plan_snapshot") or {}).get("repo") or "").lower()
        if row_repo != target and snapshot_repo != target:
            continue
        sort_key = str(row.get("updated_at") or path.stat().st_mtime)
        if sort_key >= newest_key:
            newest_key = sort_key
            newest = row
    return newest


def resolve_and_materialize_creation_preflight(
    *,
    session_id: str,
    plan: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    from aethos_core.providers.railway.deployment_plan.creation_preflight_context import (
        get_creation_preflight,
        save_creation_preflight,
    )

    session_id = (session_id or "default").strip()
    existing = get_creation_preflight(session_id=session_id)
    if existing:
        return existing

    plan = plan or {}
    preflight = load_preflight_by_plan_id(str(plan.get("plan_id") or ""))
    if not preflight and plan.get("repo"):
        preflight = load_preflight_by_repo(str(plan.get("repo") or ""))
    if preflight:
        save_creation_preflight(session_id=session_id, preflight=preflight)
        return dict(preflight)
    return None
