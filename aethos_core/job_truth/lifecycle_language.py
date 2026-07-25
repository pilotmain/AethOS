# SPDX-License-Identifier: Apache-2.0
"""Canonical job lifecycle vocabulary — Phase 11.8.0/11.8.1."""

from __future__ import annotations

from typing import Any

CANONICAL_JOB_STATES = (
    "queued",
    "dispatching",
    "running",
    "retrying",
    "awaiting_callback",
    "awaiting_follow_up",
    "verifying",
    "stabilizing",
    "completed",
    "stalled",
    "degraded",
    "failed",
    "orphaned",
    "cancelled",
)

_RAW_TO_CANONICAL: dict[str, str] = {
    "queued": "queued",
    "dispatching": "dispatching",
    "running": "running",
    "retrying": "retrying",
    "awaiting_callback": "awaiting_callback",
    "scheduled": "verifying",
    "awaiting_approval": "awaiting_follow_up",
    "completed": "completed",
    "failed": "failed",
    "cancelled": "cancelled",
    "orphaned": "orphaned",
}

_STATE_LABELS: dict[str, str] = {
    "queued": "queued",
    "dispatching": "dispatching",
    "running": "running",
    "retrying": "retrying",
    "awaiting_callback": "awaiting callback",
    "awaiting_follow_up": "awaiting follow-up",
    "verifying": "verifying",
    "stabilizing": "stabilizing",
    "completed": "completed",
    "stalled": "stalled",
    "degraded": "degraded",
    "failed": "failed",
    "orphaned": "orphaned",
    "cancelled": "cancelled",
}

_ACTIVE_STATES = {
    "queued",
    "dispatching",
    "running",
    "retrying",
    "awaiting_callback",
    "awaiting_follow_up",
    "verifying",
    "stabilizing",
}


def canonical_job_state(job: dict[str, Any], *, now: float | None = None) -> str:
    """Map persisted job record to canonical lifecycle state."""
    from aethos_core.external_execution_truth.execution_store import get_execution_meta
    from aethos_core.external_execution_truth.orphaned_job_detection import is_orphaned_execution
    from aethos_core.job_truth.stalled_job_handling import is_job_stalled

    raw = str(job.get("status") or "queued")
    job_id = str(job.get("job_id") or "")
    meta = get_execution_meta(job_id) if job_id else None

    if raw in {"completed", "failed", "cancelled", "orphaned"}:
        return _RAW_TO_CANONICAL.get(raw, raw)
    if meta and is_orphaned_execution(meta, now=now):
        return "orphaned"
    if raw == "retrying":
        return "retrying"
    if raw in {"awaiting_callback", "dispatching"}:
        return raw
    if meta and str(meta.get("runner_mode") or "") == "degraded" and raw == "running":
        return "degraded"
    if is_job_stalled(job, now=now):
        return "stalled"
    if raw == "running" and str(job.get("job_type") or "") == "recovery_window_check":
        return "stabilizing"
    if raw in {"running", "scheduled"} and str(job.get("job_type") or "") == "recovery_window_check":
        return "verifying"
    return _RAW_TO_CANONICAL.get(raw, raw)


def state_label(state: str) -> str:
    return _STATE_LABELS.get(state, state.replace("_", " "))


def describe_job_lifecycle(job: dict[str, Any], *, now: float | None = None) -> dict[str, Any]:
    state = canonical_job_state(job, now=now)
    entity = str(job.get("entity_name") or "Operational agent")
    job_type = str(job.get("job_type") or "job").replace("_", " ")
    return {
        "job_id": job.get("job_id"),
        "canonical_state": state,
        "state_label": state_label(state),
        "entity_name": entity,
        "job_type": job_type,
        "is_active": state in _ACTIVE_STATES,
        "is_terminal": state in {"completed", "failed", "cancelled"},
        "needs_attention": state in {"stalled", "degraded", "failed", "orphaned", "awaiting_callback"},
    }
