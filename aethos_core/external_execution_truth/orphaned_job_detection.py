# SPDX-License-Identifier: Apache-2.0
"""Orphaned external job detection — Phase 11.8.1."""

from __future__ import annotations

from time import time
from typing import Any

from aethos_core.external_execution_truth.callback_freshness import assess_callback_freshness
from aethos_core.external_execution_truth.execution_store import get_execution_meta, upsert_execution_meta
from aethos_core.external_execution_truth.trigger_dispatch_truth import trigger_settings
from aethos_core.jobs.job_state import get_job, list_jobs, update_job


def is_orphaned_execution(meta: dict[str, Any], *, now: float | None = None) -> bool:
    settings = trigger_settings()
    dispatched_at = meta.get("dispatched_at")
    if not dispatched_at:
        return False
    if meta.get("last_callback_at"):
        return False
    if str(meta.get("runner_mode") or "") not in {"external", "degraded"}:
        return False
    now_ts = now if now is not None else time()
    elapsed_min = (now_ts - float(dispatched_at)) / 60.0
    return elapsed_min >= settings["orphaned_job_minutes"]


def detect_orphaned_jobs(*, session_id: str | None = None, now: float | None = None) -> list[dict[str, Any]]:
    settings = trigger_settings()
    orphaned: list[dict[str, Any]] = []
    for job in list_jobs(session_id=session_id, limit=100):
        if job.get("status") in {"completed", "failed", "cancelled"}:
            continue
        meta = get_execution_meta(str(job.get("job_id") or "")) or {}
        if not meta:
            continue
        if is_orphaned_execution(meta, now=now):
            freshness = assess_callback_freshness(
                dispatched_at=meta.get("dispatched_at"),
                last_callback_at=meta.get("last_callback_at"),
                stale_callback_minutes=settings["stale_callback_minutes"],
                now=now,
            )
            orphaned.append({**job, "execution_meta": meta, "callback_freshness": freshness})
    return orphaned


def reconcile_orphaned_job(job_id: str, *, now: float | None = None) -> dict[str, Any]:
    job = get_job(job_id)
    meta = get_execution_meta(job_id)
    if not job or not meta:
        return {"ok": False, "reason": "not_found"}
    if not is_orphaned_execution(meta, now=now):
        return {"ok": True, "orphaned": False, "job_id": job_id}
    update_job(job_id, status="orphaned", error="external_execution_orphaned")
    upsert_execution_meta(job_id, orphaned=True, orphaned_at=time())
    return {"ok": True, "orphaned": True, "job_id": job_id}
