# SPDX-License-Identifier: Apache-2.0
"""Webhook reconciliation — Phase 11.8.1."""

from __future__ import annotations

from time import time
from typing import Any

from aethos_core.external_execution_truth.callback_freshness import assess_callback_freshness
from aethos_core.external_execution_truth.execution_store import get_execution_meta, upsert_execution_meta
from aethos_core.external_execution_truth.orphaned_job_detection import detect_orphaned_jobs, reconcile_orphaned_job
from aethos_core.external_execution_truth.trigger_dispatch_truth import trigger_settings
from aethos_core.jobs.job_state import get_job, update_job


def record_webhook_callback(
    *,
    job_id: str,
    status: str,
    output: dict[str, Any] | None = None,
) -> dict[str, Any]:
    job = get_job(job_id)
    if not job:
        return {"ok": False, "reason": "job_not_found"}
    meta = get_execution_meta(job_id) or {}
    now = time()
    upsert_execution_meta(
        job_id,
        session_id=job.get("session_id"),
        last_callback_at=now,
        last_callback_status=status,
        callback_count=int(meta.get("callback_count") or 0) + 1,
    )
    settings = trigger_settings()
    freshness = assess_callback_freshness(
        dispatched_at=meta.get("dispatched_at"),
        last_callback_at=now,
        stale_callback_minutes=settings["stale_callback_minutes"],
        now=now,
    )
    if status == "retrying":
        update_job(job_id, status="retrying")
    elif status == "failed":
        update_job(job_id, status="failed", error=str((output or {}).get("error") or "external_failed"))
    return {"ok": True, "job_id": job_id, "callback_freshness": freshness}


def reconcile_stale_callbacks(*, session_id: str | None = None) -> dict[str, Any]:
    settings = trigger_settings()
    actions: list[dict[str, Any]] = []
    for job in detect_orphaned_jobs(session_id=session_id):
        job_id = str(job.get("job_id") or "")
        result = reconcile_orphaned_job(job_id)
        actions.append(result)
    stale: list[dict[str, Any]] = []
    from aethos_core.external_execution_truth.execution_store import list_execution_meta

    for meta in list_execution_meta(session_id=session_id):
        job_id = str(meta.get("job_id") or "")
        job = get_job(job_id)
        if not job or job.get("status") in {"completed", "failed", "cancelled", "orphaned"}:
            continue
        freshness = assess_callback_freshness(
            dispatched_at=meta.get("dispatched_at"),
            last_callback_at=meta.get("last_callback_at"),
            stale_callback_minutes=settings["stale_callback_minutes"],
        )
        if freshness["tier"] in {"stale", "missing"}:
            stale.append({"job_id": job_id, "freshness": freshness})
    return {"ok": True, "orphaned_actions": actions, "stale_callbacks": stale}
