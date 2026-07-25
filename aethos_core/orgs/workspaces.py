# SPDX-License-Identifier: Apache-2.0
"""Workspaces — scoped operational areas within organizations."""

from __future__ import annotations

import json
from time import time
from typing import Any
from uuid import uuid4

from aethos_core.orgs.organizations import get_current_organization
from aethos_core.orgs.paths import orgs_root


def _path():
    return orgs_root() / "workspaces.json"


def _load() -> dict[str, Any]:
    if not _path().is_file():
        return {"workspaces": {}}
    try:
        return json.loads(_path().read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"workspaces": {}}


def _save(data: dict[str, Any]) -> None:
    _path().write_text(json.dumps(data, indent=2), encoding="utf-8")


def list_workspaces(*, org_id: str | None = None) -> list[dict[str, Any]]:
    oid = org_id or get_current_organization().get("org_id")
    rows = [w for w in (_load().get("workspaces") or {}).values() if w.get("org_id") == oid]
    rows.sort(key=lambda w: float(w.get("created_at") or 0), reverse=True)
    return rows


def register_workspace(*, name: str, org_id: str | None = None, repo_hint: str = "aethos") -> dict[str, Any]:
    oid = org_id or get_current_organization().get("org_id")
    ws_id = f"ws-{uuid4().hex[:10]}"
    record = {
        "workspace_id": ws_id,
        "org_id": oid,
        "name": name,
        "repo_hint": repo_hint,
        "created_at": time(),
        "status": "active",
    }
    data = _load()
    workspaces = dict(data.get("workspaces") or {})
    workspaces[ws_id] = record
    data["workspaces"] = workspaces
    _save(data)
    return record
