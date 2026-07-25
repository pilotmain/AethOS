# SPDX-License-Identifier: Apache-2.0
"""Per-step execution checkpoints."""

from __future__ import annotations

from typing import Any

from aethos_core.autonomous_execution import execution_plan


def save_checkpoint(
    st: dict[str, Any],
    plan_id: str,
    step_id: str,
    *,
    task_id: str = "",
    outputs: list[Any] | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    root = execution_plan.execution_root(st)
    cps = root.setdefault("checkpoints", {})
    if not isinstance(cps, dict):
        root["checkpoints"] = {}
        cps = root["checkpoints"]
    plan_cp = cps.setdefault(plan_id, {})
    if not isinstance(plan_cp, dict):
        cps[plan_id] = {}
        plan_cp = cps[plan_id]
    row: dict[str, Any] = {"step_id": step_id, "outputs": list(outputs or [])}
    if metadata:
        row["metadata"] = dict(metadata)
    plan_cp[step_id] = row
    _ = task_id


def get_checkpoint(st: dict[str, Any], plan_id: str, step_id: str) -> dict[str, Any] | None:
    cps = execution_plan.execution_root(st).get("checkpoints") or {}
    if not isinstance(cps, dict):
        return None
    plan_cp = cps.get(plan_id)
    if not isinstance(plan_cp, dict):
        return None
    row = plan_cp.get(step_id)
    return row if isinstance(row, dict) else None
