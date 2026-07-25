# SPDX-License-Identifier: Apache-2.0
"""Execute simple orchestration tasks without execution plans."""

from __future__ import annotations

from typing import Any

from aethos_core.autonomous_execution import task_registry


def execute_task(st: dict[str, Any], task_id: str) -> str:
    task = task_registry.get_task(st, task_id)
    if not task:
        return "failed"
    typ = str(task.get("type") or "noop")
    if typ == "noop":
        orch = st.setdefault("orchestration", {})
        cp = orch.setdefault("checkpoints", {})
        if isinstance(cp, dict):
            cp[task_id] = {"step": "done", "outputs": task.get("outputs") or []}
        return "completed"
    return "failed"
