# SPDX-License-Identifier: Apache-2.0
"""Persistent multi-step execution plans."""

from __future__ import annotations

import time
import uuid
from typing import Any


def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def execution_root(st: dict[str, Any]) -> dict[str, Any]:
    ex = st.setdefault("execution", {})
    if not isinstance(ex, dict):
        st["execution"] = {}
        return st["execution"]
    return ex


def plans(st: dict[str, Any]) -> dict[str, Any]:
    p = execution_root(st).setdefault("plans", {})
    if not isinstance(p, dict):
        execution_root(st)["plans"] = {}
        return execution_root(st)["plans"]
    return p


def create_plan(st: dict[str, Any], task_id: str, steps: list[dict[str, Any]]) -> str:
    plan_id = str(uuid.uuid4())
    norm_steps: list[dict[str, Any]] = []
    for raw in steps:
        s = dict(raw)
        sid = str(s.get("step_id") or uuid.uuid4())
        s["step_id"] = sid
        s.setdefault("status", "queued")
        s.setdefault("depends_on", [])
        if not isinstance(s["depends_on"], list):
            s["depends_on"] = []
        s.setdefault("retry_count", 0)
        s.setdefault("outputs", [])
        s.setdefault("type", str(s.get("type") or "noop"))
        s.setdefault("retryable", True)
        s.setdefault("max_retries", 3)
        norm_steps.append(s)
    plans(st)[plan_id] = {
        "plan_id": plan_id,
        "task_id": task_id,
        "status": "active",
        "created_at": _now_iso(),
        "updated_at": _now_iso(),
        "steps": norm_steps,
    }
    return plan_id


def get_plan(st: dict[str, Any], plan_id: str) -> dict[str, Any] | None:
    p = plans(st).get(plan_id)
    return p if isinstance(p, dict) else None


def get_step(plan: dict[str, Any], step_id: str) -> dict[str, Any] | None:
    for s in plan.get("steps") or []:
        if isinstance(s, dict) and str(s.get("step_id")) == step_id:
            return s
    return None


def update_plan_timestamp(plan: dict[str, Any]) -> None:
    plan["updated_at"] = _now_iso()


def all_steps_terminal(plan: dict[str, Any]) -> bool:
    terminal = frozenset({"completed", "failed", "cancelled"})
    steps = plan.get("steps") or []
    if not steps:
        return False
    return all(isinstance(s, dict) and str(s.get("status") or "") in terminal for s in steps)


def any_step_failed(plan: dict[str, Any]) -> bool:
    return any(isinstance(s, dict) and str(s.get("status") or "") == "failed" for s in plan.get("steps") or [])
