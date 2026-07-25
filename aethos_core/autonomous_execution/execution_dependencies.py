# SPDX-License-Identifier: Apache-2.0
"""Dependency ordering for execution plan steps."""

from __future__ import annotations

from typing import Any


def _completed_ids(plan: dict[str, Any]) -> set[str]:
    return {
        str(s.get("step_id"))
        for s in plan.get("steps") or []
        if isinstance(s, dict) and str(s.get("status") or "") == "completed" and s.get("step_id")
    }


def dependencies_satisfied(plan: dict[str, Any], step: dict[str, Any]) -> bool:
    done = _completed_ids(plan)
    return all(str(dep) in done for dep in step.get("depends_on") or [])


def validate_plan_dependency_dag(plan: dict[str, Any]) -> bool:
    steps = [s for s in (plan.get("steps") or []) if isinstance(s, dict)]
    ids = {str(s.get("step_id")) for s in steps if s.get("step_id")}
    indeg = {i: 0 for i in ids}
    adj = {i: [] for i in ids}
    for s in steps:
        sid = str(s.get("step_id"))
        if sid not in indeg:
            continue
        for dep in s.get("depends_on") or []:
            d = str(dep)
            if d not in ids:
                continue
            adj[d].append(sid)
            indeg[sid] += 1
    queue = [i for i in ids if indeg[i] == 0]
    seen = 0
    while queue:
        u = queue.pop()
        seen += 1
        for v in adj.get(u, []):
            indeg[v] -= 1
            if indeg[v] == 0:
                queue.append(v)
    return seen == len(ids)


def ready_steps(plan: dict[str, Any], *, now_ts: float | None = None) -> list[dict[str, Any]]:
    _ = now_ts
    out: list[dict[str, Any]] = []
    for s in plan.get("steps") or []:
        if not isinstance(s, dict):
            continue
        if str(s.get("status") or "") == "queued" and dependencies_satisfied(plan, s):
            out.append(s)
    return out
