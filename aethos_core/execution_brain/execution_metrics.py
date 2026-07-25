# SPDX-License-Identifier: Apache-2.0
"""Execution brain metrics — task completion and recovery tracking."""

from __future__ import annotations

from aethos_core.execution_brain.execution_memory import load_execution_memory


def execution_brain_metrics(*, session_id: str = "default") -> dict[str, int | str | list[str]]:
    record = load_execution_memory(session_id=session_id)
    metrics = dict(record.metrics)
    return {
        "session_id": session_id,
        "active_goal": record.active_goal,
        "provider": record.provider,
        "steps_completed": len(record.completed_steps),
        "prior_failures": list(record.prior_failures),
        "active_job_id": record.active_job_id,
        "last_blocker_code": record.last_blocker_code,
        "brain_turn_completed": metrics.get("brain_turn_completed", 0),
        "brain_turn_blocked": metrics.get("brain_turn_blocked", 0),
        "brain_turn_awaiting_approval": metrics.get("brain_turn_awaiting_approval", 0),
    }
