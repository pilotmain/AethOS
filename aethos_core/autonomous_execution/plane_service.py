# SPDX-License-Identifier: Apache-2.0
"""Public service for submitting and dispatching autonomous tasks."""

from __future__ import annotations

from typing import Any

from aethos_core.autonomous_execution import (
    execution_plan,
    runtime_dispatcher,
    runtime_state,
    task_queue,
    task_registry,
)
from aethos_core.config import get_settings


def _plane_enabled() -> bool:
    return bool(getattr(get_settings(), "autonomous_execution_plane_enabled", False))


def submit_noop_task(*, owner: str = "operator", outputs: list[Any] | None = None) -> dict[str, Any]:
    if not _plane_enabled():
        return {"ok": False, "error": "autonomous_execution_plane_disabled"}
    st = runtime_state.load_runtime_state()
    tid = task_registry.put_task(
        st,
        {"type": "noop", "state": "queued", "owner": owner, "outputs": list(outputs or [])},
    )
    task_queue.enqueue_task_id(st, "execution_queue", tid)
    runtime_state.save_runtime_state(st)
    return {"ok": True, "task_id": tid}


def submit_planned_task(
    *,
    steps: list[dict[str, Any]],
    owner: str = "operator",
    task_type: str = "planned",
) -> dict[str, Any]:
    if not _plane_enabled():
        return {"ok": False, "error": "autonomous_execution_plane_disabled"}
    if not steps:
        return {"ok": False, "error": "steps_required"}
    st = runtime_state.load_runtime_state()
    tid = task_registry.put_task(st, {"type": task_type, "state": "queued", "owner": owner})
    plan_id = execution_plan.create_plan(st, tid, steps)
    task_registry.update_task_state(st, tid, "queued", execution_plan_id=plan_id)
    task_queue.enqueue_task_id(st, "execution_queue", tid)
    runtime_state.save_runtime_state(st)
    return {"ok": True, "task_id": tid, "execution_plan_id": plan_id}


def dispatch_until_idle(*, max_ticks: int = 32) -> dict[str, Any]:
    if not _plane_enabled():
        return {"ok": False, "error": "autonomous_execution_plane_disabled", "ticks": 0, "results": []}
    st = runtime_state.load_runtime_state()
    results: list[dict[str, Any]] = []
    ticks = 0
    while ticks < max_ticks:
        res = runtime_dispatcher.dispatch_once(st)
        if res is None:
            break
        results.append(res)
        ticks += 1
    runtime_state.save_runtime_state(st)
    return {"ok": True, "ticks": ticks, "results": results}


def plane_status_snapshot() -> dict[str, Any]:
    st = runtime_state.load_runtime_state()
    active = task_registry.count_by_states(st, {"queued", "running", "waiting", "retrying"})
    completed = task_registry.count_by_states(st, {"completed"})
    failed = task_registry.count_by_states(st, {"failed"})
    return {
        "ok": True,
        "enabled": _plane_enabled(),
        "path": str(runtime_state.operator_runtime_path()),
        "queue_depth": task_queue.queue_len(st, "execution_queue"),
        "active_tasks": active,
        "completed_tasks": completed,
        "failed_tasks": failed,
        "supervisor": execution_plan.execution_root(st).get("supervisor") or {},
    }
