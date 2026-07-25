# SPDX-License-Identifier: Apache-2.0
"""
Persistent subagent session store — session-key keyed.

Key shape: `agent:{parent_session_id}:subagent:{spawn_id}` + JSON store + message log
"""

from __future__ import annotations

import json
import re
from time import time
from typing import Any
from uuid import uuid4

from aethos_core.agents.runtime.paths import agent_artifacts_root

_STORE_FILE = "subagent_sessions.json"
_SESSION_KEY_RE = re.compile(r"^agent:[a-zA-Z0-9._-]+:subagent:[a-zA-Z0-9._-]+$")


def build_subagent_session_key(*, parent_session_id: str, spawn_id: str) -> str:
    parent = _sanitize_segment(parent_session_id or "default")
    spawn = _sanitize_segment(spawn_id)
    return f"agent:{parent}:subagent:{spawn}"


def is_subagent_session_key(session_key: str) -> bool:
    return bool(_SESSION_KEY_RE.match((session_key or "").strip()))


def _sanitize_segment(value: str) -> str:
    raw = (value or "default").strip().lower()
    cleaned = re.sub(r"[^a-z0-9._-]+", "-", raw).strip("-")
    return cleaned[:64] or "default"


def _store_path():
    return agent_artifacts_root() / _STORE_FILE


def _load() -> dict[str, Any]:
    path = _store_path()
    if not path.is_file():
        return {"sessions": {}, "updated_at": None}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"sessions": {}, "updated_at": None}


def _save(data: dict[str, Any]) -> None:
    data["updated_at"] = time()
    path = _store_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def create_subagent_session(
    *,
    parent_session_id: str,
    goal: str,
    workspace_hint: str | None = None,
    spawn_id: str | None = None,
    role_label: str | None = None,
    capability: str | None = None,
    attached_skills: list[str] | None = None,
    tenant_id: str | None = None,
    initial_transcript: list[dict[str, Any]] | None = None,
    spawn_status: str = "active",
) -> dict[str, Any]:
    sid = spawn_id or f"spawn-{uuid4().hex[:12]}"
    session_key = build_subagent_session_key(parent_session_id=parent_session_id, spawn_id=sid)
    now = time()
    tid = None
    if tenant_id is not None:
        from aethos_core.tenancy.tenant_data_store import resolve_data_tenant

        tid = resolve_data_tenant(tenant_id)
    row = {
        "session_key": session_key,
        "spawn_id": sid,
        "parent_session_id": parent_session_id,
        "goal": goal.strip(),
        "workspace_hint": workspace_hint,
        "role_label": (role_label or "").strip() or None,
        "capability": (capability or "").strip() or None,
        "attached_skills": list(attached_skills or []),
        "tenant_id": tid,
        "status": (spawn_status or "active").strip() or "active",
        "run_count": 0,
        "plan_id": None,
        "coordination_artifact_id": None,
        "summary_artifact_id": None,
        "messages": [
            {
                "role": "user",
                "content": goal.strip(),
                "at": now,
                "source_tool": "agent_spawn",
                "provenance": {"kind": "spawn", "source_tool": "agent_spawn"},
            }
        ],
        "runs": [],
        "transcript": list(initial_transcript or []),
        "terminal_preflight_ids": [],
        "created_at": now,
        "updated_at": now,
        "read_only": True,
        "mutation_execution_enabled": False,
    }
    data = _load()
    sessions = dict(data.get("sessions") or {})
    sessions[session_key] = row
    data["sessions"] = sessions
    _save(data)
    return dict(row)


def get_subagent_session(session_key: str) -> dict[str, Any] | None:
    key = (session_key or "").strip()
    if not key:
        return None
    row = (_load().get("sessions") or {}).get(key)
    return dict(row) if isinstance(row, dict) else None


def get_subagent_session_by_spawn_id(spawn_id: str, *, parent_session_id: str | None = None) -> dict[str, Any] | None:
    needle = (spawn_id or "").strip()
    if not needle:
        return None
    if parent_session_id:
        key = build_subagent_session_key(parent_session_id=parent_session_id, spawn_id=needle)
        return get_subagent_session(key)
    for row in list_subagent_sessions(limit=200):
        if row.get("spawn_id") == needle:
            return row
    return None


def list_subagent_sessions(*, parent_session_id: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
    sessions = dict(_load().get("sessions") or {})
    rows = [dict(v) for v in sessions.values() if isinstance(v, dict)]
    if parent_session_id:
        parent = (parent_session_id or "").strip()
        rows = [r for r in rows if str(r.get("parent_session_id") or "") == parent]
    rows.sort(key=lambda r: float(r.get("updated_at") or 0), reverse=True)
    return rows[: max(1, min(limit, 200))]


def append_subagent_message(
    session_key: str,
    *,
    role: str,
    content: str,
    source_tool: str = "agent_send",
) -> dict[str, Any] | None:
    data = _load()
    sessions = dict(data.get("sessions") or {})
    row = sessions.get(session_key)
    if not isinstance(row, dict):
        return None
    now = time()
    messages = list(row.get("messages") or [])
    messages.append(
        {
            "role": role,
            "content": content.strip(),
            "at": now,
            "source_tool": source_tool,
            "provenance": {"kind": "inter_session", "source_tool": source_tool},
        }
    )
    row["messages"] = messages[-100:]
    row["updated_at"] = now
    sessions[session_key] = row
    data["sessions"] = sessions
    _save(data)
    return dict(row)


def record_subagent_run(
    session_key: str,
    *,
    outcome: dict[str, Any],
    goal_snapshot: str,
    transcript: list[dict[str, Any]] | None = None,
) -> dict[str, Any] | None:
    data = _load()
    sessions = dict(data.get("sessions") or {})
    row = sessions.get(session_key)
    if not isinstance(row, dict):
        return None
    now = time()
    plan = outcome.get("plan") or {}
    runs = list(row.get("runs") or [])
    runs.append(
        {
            "at": now,
            "plan_id": plan.get("plan_id"),
            "goal_snapshot": goal_snapshot[:2000],
            "status": (outcome.get("merged") or {}).get("status") or outcome.get("status"),
            "coordination_artifact_id": outcome.get("coordination_artifact_id"),
            "duration_ms": outcome.get("duration_ms"),
        }
    )
    row["runs"] = runs[-20:]
    row["run_count"] = len(row["runs"])
    row["plan_id"] = plan.get("plan_id")
    row["status"] = str((outcome.get("merged") or {}).get("status") or "completed")
    row["coordination_artifact_id"] = outcome.get("coordination_artifact_id")
    row["summary_artifact_id"] = outcome.get("summary_artifact_id")
    row["transcript"] = transcript if transcript is not None else list(outcome.get("transcript") or [])
    row["updated_at"] = now
    report = str(outcome.get("report") or "")
    if report:
        messages = list(row.get("messages") or [])
        messages.append(
            {
                "role": "assistant",
                "content": report[:8000],
                "at": now,
                "source_tool": "agent_coordination",
                "provenance": {"kind": "inter_session", "source_tool": "agent_coordination"},
            }
        )
        row["messages"] = messages[-100:]
    sessions[session_key] = row
    data["sessions"] = sessions
    _save(data)
    return dict(row)


def link_terminal_preflight(session_key: str, preflight_id: str) -> dict[str, Any] | None:
    data = _load()
    sessions = dict(data.get("sessions") or {})
    row = sessions.get(session_key)
    if not isinstance(row, dict):
        return None
    ids = list(row.get("terminal_preflight_ids") or [])
    if preflight_id not in ids:
        ids.append(preflight_id)
    row["terminal_preflight_ids"] = ids[-20:]
    row["updated_at"] = time()
    sessions[session_key] = row
    data["sessions"] = sessions
    _save(data)
    return dict(row)


def clear_subagent_sessions_for_tests() -> None:
    path = _store_path()
    if path.is_file():
        path.unlink()
