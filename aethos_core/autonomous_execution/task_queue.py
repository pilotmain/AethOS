# SPDX-License-Identifier: Apache-2.0
"""Named persistent task queues in operator runtime state."""

from __future__ import annotations

from typing import Any

QUEUE_NAMES = (
    "execution_queue",
    "recovery_queue",
)


def ensure_queue(st: dict[str, Any], name: str) -> list[Any]:
    q = st.setdefault(name, [])
    if not isinstance(q, list):
        st[name] = []
        return st[name]
    return q


def enqueue_task_id(st: dict[str, Any], queue_name: str, task_id: str) -> None:
    from aethos_core.config import get_settings

    lim = int(getattr(get_settings(), "aethos_queue_limit", 500) or 500)
    q = ensure_queue(st, queue_name)
    if len(q) >= lim:
        metrics = st.setdefault("runtime_metrics", {})
        if isinstance(metrics, dict):
            metrics["queue_pressure_events_total"] = int(metrics.get("queue_pressure_events_total") or 0) + 1
        return
    if task_id not in q:
        q.append(task_id)


def dequeue_task_id(st: dict[str, Any], queue_name: str) -> str | None:
    q = ensure_queue(st, queue_name)
    if not q:
        return None
    tid = q.pop(0)
    return str(tid) if tid is not None else None


def queue_len(st: dict[str, Any], queue_name: str) -> int:
    return len(ensure_queue(st, queue_name))
