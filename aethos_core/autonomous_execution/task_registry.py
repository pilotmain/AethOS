# SPDX-License-Identifier: Apache-2.0
"""Persistent task registry."""

from __future__ import annotations

import time
import uuid
from typing import Any

TASK_STATES = frozenset(
    {
        "queued",
        "scheduled",
        "running",
        "waiting",
        "blocked",
        "retrying",
        "completed",
        "failed",
        "cancelled",
        "recovering",
    }
)


def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def registry(st: dict[str, Any]) -> dict[str, Any]:
    tr = st.setdefault("task_registry", {})
    if not isinstance(tr, dict):
        st["task_registry"] = {}
        return st["task_registry"]
    return tr


def put_task(st: dict[str, Any], task: dict[str, Any]) -> str:
    tid = str(task.get("id") or uuid.uuid4())
    row = dict(task)
    row["id"] = tid
    row.setdefault("created_at", _now_iso())
    row["updated_at"] = _now_iso()
    state = str(row.get("state") or "queued")
    if state not in TASK_STATES:
        state = "queued"
    row["state"] = state
    registry(st)[tid] = row
    return tid


def get_task(st: dict[str, Any], task_id: str) -> dict[str, Any] | None:
    t = registry(st).get(task_id)
    return t if isinstance(t, dict) else None


def update_task_state(st: dict[str, Any], task_id: str, state: str, **extra: Any) -> None:
    t = get_task(st, task_id)
    if not t:
        return
    if state in TASK_STATES:
        t["state"] = state
    t["updated_at"] = _now_iso()
    for key, value in extra.items():
        t[key] = value


def count_by_states(st: dict[str, Any], states: set[str]) -> int:
    return sum(
        1
        for t in registry(st).values()
        if isinstance(t, dict) and str(t.get("state")) in states
    )


def list_task_ids_by_state(st: dict[str, Any], state: str) -> list[str]:
    return [
        str(tid)
        for tid, t in registry(st).items()
        if isinstance(t, dict) and str(t.get("state")) == state
    ]
