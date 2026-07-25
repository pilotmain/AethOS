# SPDX-License-Identifier: Apache-2.0
"""Execution memory — session-scoped goal and workflow state."""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import Any

_lock = threading.Lock()
_store: dict[str, "ExecutionMemoryRecord"] = {}


@dataclass
class ExecutionMemoryRecord:
    session_id: str
    active_goal: str = ""
    provider: str = ""
    step_index: int = 0
    completed_steps: list[str] = field(default_factory=list)
    prior_failures: list[str] = field(default_factory=list)
    discovered_resources: dict[str, Any] = field(default_factory=dict)
    approvals: dict[str, bool] = field(default_factory=dict)
    active_job_id: str = ""
    last_blocker_code: str = ""
    metrics: dict[str, int] = field(default_factory=dict)


def load_execution_memory(*, session_id: str = "default") -> ExecutionMemoryRecord:
    sid = (session_id or "default").strip() or "default"
    with _lock:
        record = _store.get(sid)
        if record is None:
            record = ExecutionMemoryRecord(session_id=sid)
            _store[sid] = record
        return record


def save_execution_memory(record: ExecutionMemoryRecord) -> None:
    with _lock:
        _store[record.session_id] = record


def update_execution_memory(
    *,
    session_id: str,
    goal: str = "",
    provider: str = "",
    step_completed: str = "",
    failure_code: str = "",
    discovered: dict[str, Any] | None = None,
    job_id: str = "",
    increment_metric: str = "",
) -> ExecutionMemoryRecord:
    record = load_execution_memory(session_id=session_id)
    if goal:
        record.active_goal = goal
    if provider:
        record.provider = provider
    if step_completed and step_completed not in record.completed_steps:
        record.completed_steps.append(step_completed)
        record.step_index = len(record.completed_steps)
    if failure_code:
        record.last_blocker_code = failure_code
        if failure_code not in record.prior_failures:
            record.prior_failures.append(failure_code)
    if discovered:
        record.discovered_resources.update(discovered)
    if job_id:
        record.active_job_id = job_id
    if increment_metric:
        record.metrics[increment_metric] = record.metrics.get(increment_metric, 0) + 1
    save_execution_memory(record)
    return record


def clear_execution_memory_for_tests() -> None:
    with _lock:
        _store.clear()
