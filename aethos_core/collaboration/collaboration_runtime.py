# SPDX-License-Identifier: Apache-2.0
"""Human-agent collaboration runtime."""

from __future__ import annotations

import json
from time import time
from typing import Any
from uuid import uuid4

from pathlib import Path


def _store_path() -> Path:
    root = Path(__file__).resolve().parents[2] / "data" / "collaboration"
    root.mkdir(parents=True, exist_ok=True)
    return root / "sessions.json"


def _load() -> list[dict[str, Any]]:
    path = _store_path()
    if not path.is_file():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []


def _save(rows: list[dict[str, Any]]) -> None:
    _store_path().write_text(json.dumps(rows[:50], indent=2), encoding="utf-8")


def start_collaboration_session(*, operator_id: str = "default", focus: str = "investigation", context: str = "") -> dict[str, Any]:
    session_id = f"collab-{uuid4().hex[:10]}"
    record = {
        "session_id": session_id,
        "operator_id": operator_id,
        "focus": focus,
        "context": context[:300],
        "status": "active",
        "checkpoints": [],
        "agent_handoffs": [],
        "started_at": time(),
        "human_authoritative": True,
        "autonomous_execution_blocked": True,
    }
    rows = _load()
    rows.insert(0, record)
    _save(rows)
    return {"ok": True, "session": record}


def add_checkpoint(*, session_id: str, label: str, approved: bool = False) -> dict[str, Any]:
    rows = _load()
    for row in rows:
        if row.get("session_id") == session_id:
            cp = {"label": label, "approved": approved, "at": time()}
            row.setdefault("checkpoints", []).append(cp)
            _save(rows)
            return {"ok": True, "checkpoint": cp, "session_id": session_id}
    return {"ok": False, "reason": "Session not found."}


def agent_handoff(*, session_id: str, from_agent: str, to_agent: str, scope: str) -> dict[str, Any]:
    rows = _load()
    for row in rows:
        if row.get("session_id") == session_id:
            handoff = {
                "from": from_agent,
                "to": to_agent,
                "scope": scope[:200],
                "bounded": True,
                "at": time(),
            }
            row.setdefault("agent_handoffs", []).append(handoff)
            _save(rows)
            return {"ok": True, "handoff": handoff, "human_authoritative": True}
    return {"ok": False, "reason": "Session not found."}


def list_collaboration_sessions(*, operator_id: str | None = None) -> dict[str, Any]:
    rows = _load()
    if operator_id:
        rows = [r for r in rows if r.get("operator_id") == operator_id]
    return {"ok": True, "sessions": rows, "principle": "Agents assist. Humans remain authoritative."}


def clear_collaboration_for_tests() -> None:
    path = _store_path()
    if path.is_file():
        path.unlink()
