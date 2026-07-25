# SPDX-License-Identifier: Apache-2.0
"""Workspace sessions — bounded runtime sessions."""

from __future__ import annotations

import json
from time import time
from typing import Any
from uuid import uuid4

from aethos_core.workspace_runtime.paths import workspace_runtime_root


def create_workspace_session(*, workspace_id: str | None, kind: str = "terminal") -> dict[str, Any]:
    session_id = f"wsess-{uuid4().hex[:12]}"
    record = {
        "session_id": session_id,
        "workspace_id": workspace_id,
        "kind": kind,
        "status": "active",
        "created_at": time(),
        "readonly": False,
        "autonomous_execution_blocked": True,
    }
    _save_session(session_id, record)
    return record


def get_workspace_session(session_id: str) -> dict[str, Any] | None:
    path = workspace_runtime_root() / "sessions" / f"{session_id}.json"
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def list_workspace_sessions(*, limit: int = 20) -> list[dict[str, Any]]:
    root = workspace_runtime_root() / "sessions"
    if not root.is_dir():
        return []
    rows: list[dict[str, Any]] = []
    for path in sorted(root.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            rows.append(json.loads(path.read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError):
            continue
        if len(rows) >= limit:
            break
    return rows


def close_workspace_session(session_id: str) -> dict[str, Any]:
    row = get_workspace_session(session_id)
    if not row:
        return {"ok": False, "error": "not_found"}
    row["status"] = "closed"
    row["closed_at"] = time()
    _save_session(session_id, row)
    return {"ok": True, "session": row}


def _save_session(session_id: str, record: dict[str, Any]) -> None:
    root = workspace_runtime_root() / "sessions"
    root.mkdir(parents=True, exist_ok=True)
    (root / f"{session_id}.json").write_text(json.dumps(record, indent=2), encoding="utf-8")


def clear_workspace_sessions_for_tests() -> None:
    root = workspace_runtime_root() / "sessions"
    if root.is_dir():
        for p in root.glob("*.json"):
            p.unlink()
