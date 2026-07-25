# SPDX-License-Identifier: Apache-2.0
"""Stalled job handling — Phase 11.8.0."""

from __future__ import annotations

from time import time
from typing import Any

STALLED_RUNNING_SECONDS = 900  # 15m without update while running
STALLED_QUEUED_SECONDS = 1800  # 30m queued


def is_job_stalled(job: dict[str, Any], *, now: float | None = None) -> bool:
    now_ts = now if now is not None else time()
    status = str(job.get("status") or "")
    if status not in {"queued", "running", "scheduled"}:
        return False
    anchor = job.get("updated_at") or job.get("started_at") or job.get("created_at")
    if not anchor:
        return False
    elapsed = now_ts - float(anchor)
    if status == "queued":
        return elapsed >= STALLED_QUEUED_SECONDS
    return elapsed >= STALLED_RUNNING_SECONDS


def describe_stalled_job(job: dict[str, Any], *, now: float | None = None) -> str:
    from aethos_core.job_truth.activity_truth import describe_last_activity

    entity = str(job.get("entity_name") or "Operational agent")
    job_type = str(job.get("job_type") or "job").replace("_", " ")
    activity = describe_last_activity(job, now=now)
    return (
        f"**{entity}** ({job_type}) has not progressed since "
        f"{activity['last_activity_phrase']}. "
        "This is a stalled background job — not active thinking. "
        "Ask to retry or inspect the latest artifact if you need a fresh pass."
    )
