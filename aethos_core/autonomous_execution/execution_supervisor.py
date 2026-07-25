# SPDX-License-Identifier: Apache-2.0
"""Advance planned autonomous tasks one step at a time."""

from __future__ import annotations

import time
from typing import Any

from aethos_core.autonomous_execution import (
    execution_checkpoint,
    execution_dependencies,
    execution_plan,
    task_registry,
    tool_step,
)


def _note_supervisor(st: dict[str, Any], *, error: str | None = None) -> None:
    sup = execution_plan.execution_root(st).setdefault("supervisor", {})
    if not isinstance(sup, dict):
        execution_plan.execution_root(st)["supervisor"] = {}
        sup = execution_plan.execution_root(st)["supervisor"]
    sup["ticks"] = int(sup.get("ticks") or 0) + 1
    sup["last_tick"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    if error:
        sup["last_error"] = error


def tick_planned_task(
    st: dict[str, Any],
    task_id: str,
    *,
    source_queue: str | None = None,
) -> dict[str, Any] | None:
    task = task_registry.get_task(st, task_id)
    if not task:
        return None
    plan_id = task.get("execution_plan_id")
    if not plan_id:
        return None
    plan = execution_plan.get_plan(st, str(plan_id))
    if not plan:
        task_registry.update_task_state(st, task_id, "failed", reason="missing_execution_plan")
        _note_supervisor(st, error="missing_plan")
        return {"terminal": "failed", "plan_id": str(plan_id), "reason": "missing_plan"}

    if not execution_dependencies.validate_plan_dependency_dag(plan):
        task_registry.update_task_state(st, task_id, "failed", reason="invalid_dependency_dag")
        _note_supervisor(st, error="dependency_cycle")
        return {"terminal": "failed", "plan_id": str(plan_id), "reason": "dependency_cycle"}

    _note_supervisor(st)

    if execution_plan.any_step_failed(plan):
        task_registry.update_task_state(st, task_id, "failed")
        plan["status"] = "failed"
        execution_plan.update_plan_timestamp(plan)
        return {"terminal": "failed", "plan_id": str(plan_id)}

    if execution_plan.all_steps_terminal(plan):
        task_registry.update_task_state(st, task_id, "completed")
        plan["status"] = "completed"
        execution_plan.update_plan_timestamp(plan)
        return {"terminal": "completed", "plan_id": str(plan_id)}

    ready = execution_dependencies.ready_steps(plan)
    if not ready:
        task_registry.update_task_state(st, task_id, "waiting")
        execution_plan.update_plan_timestamp(plan)
        return {"terminal": "waiting", "plan_id": str(plan_id)}

    step = ready[0]
    step_id = str(step.get("step_id"))
    step["status"] = "running"
    result = tool_step.execute_tool_step(step)
    ok = bool(result.get("ok"))
    if ok:
        step["status"] = "completed"
        step["outputs"] = list(step.get("outputs") or []) + [result]
        execution_checkpoint.save_checkpoint(
            st,
            str(plan_id),
            step_id,
            task_id=task_id,
            outputs=list(step.get("outputs") or []),
            metadata={"source_queue": source_queue or ""},
        )
        execution_plan.update_plan_timestamp(plan)
        if execution_plan.all_steps_terminal(plan):
            task_registry.update_task_state(st, task_id, "completed")
            plan["status"] = "completed"
            return {"terminal": "completed", "plan_id": str(plan_id)}
        task_registry.update_task_state(st, task_id, "running")
        return {"terminal": "running", "plan_id": str(plan_id), "step_id": step_id}

    step["status"] = "failed"
    step["error"] = str(result.get("error") or "tool_failed")
    execution_checkpoint.save_checkpoint(
        st,
        str(plan_id),
        step_id,
        task_id=task_id,
        outputs=[result],
        metadata={"failed": True},
    )
    task_registry.update_task_state(st, task_id, "failed")
    plan["status"] = "failed"
    execution_plan.update_plan_timestamp(plan)
    return {"terminal": "failed", "plan_id": str(plan_id), "step_id": step_id}
