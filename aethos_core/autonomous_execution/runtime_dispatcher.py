# SPDX-License-Identifier: Apache-2.0
"""Pop one task from queues and execute it."""

from __future__ import annotations

from typing import Any

from aethos_core.autonomous_execution import (
    execution_supervisor,
    runtime_executor,
    task_queue,
    task_registry,
)


def _pick_next_task_id(st: dict[str, Any]) -> tuple[str | None, str | None]:
    for qname in ("recovery_queue", "execution_queue"):
        tid = task_queue.dequeue_task_id(st, qname)
        if tid:
            return tid, qname
    return None, None


def dispatch_once(st: dict[str, Any]) -> dict[str, Any] | None:
    tid, src = _pick_next_task_id(st)
    if not tid:
        return None
    task = task_registry.get_task(st, tid)
    if not task:
        return {"task_id": tid, "skipped": True, "reason": "missing_task"}

    if task.get("execution_plan_id"):
        plan_res = execution_supervisor.tick_planned_task(st, tid, source_queue=src or "")
        term = str(plan_res.get("terminal") or "failed") if plan_res else "failed"
        if term in ("running", "waiting", "retrying"):
            task_queue.enqueue_task_id(st, "execution_queue", tid)
        return {"task_id": tid, "terminal": term, "planned": True, **(plan_res or {})}

    prev = str(task.get("state") or "queued")
    if prev in ("queued", "scheduled"):
        task_registry.update_task_state(st, tid, "running")
    terminal = runtime_executor.execute_task(st, tid)
    task_registry.update_task_state(st, tid, terminal)
    return {"task_id": tid, "terminal": terminal, "planned": False}
