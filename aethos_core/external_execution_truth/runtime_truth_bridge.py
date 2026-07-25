# SPDX-License-Identifier: Apache-2.0
"""External execution → operational memory bridge — Phase 11.8.1."""

from __future__ import annotations

from typing import Any

from aethos_core.external_execution_truth.callback_freshness import assess_callback_freshness
from aethos_core.external_execution_truth.degraded_execution_language import (
    describe_awaiting_callback,
    describe_orphaned_execution,
)
from aethos_core.external_execution_truth.execution_store import get_execution_meta, list_execution_meta
from aethos_core.external_execution_truth.external_runner_presence import assess_external_runner_presence
from aethos_core.external_execution_truth.orphaned_job_detection import detect_orphaned_jobs
from aethos_core.external_execution_truth.retry_truth import describe_retry_state
from aethos_core.external_execution_truth.trigger_dispatch_truth import trigger_settings
from aethos_core.jobs.job_state import get_job


def enrich_job_with_execution_truth(job: dict[str, Any], *, now: float | None = None) -> dict[str, Any]:
    job_id = str(job.get("job_id") or "")
    meta = get_execution_meta(job_id) or {}
    settings = trigger_settings()
    freshness = assess_callback_freshness(
        dispatched_at=meta.get("dispatched_at"),
        last_callback_at=meta.get("last_callback_at"),
        stale_callback_minutes=settings["stale_callback_minutes"],
        now=now,
    )
    retry = describe_retry_state(
        retries=int(job.get("retries") or 0),
        max_retries=settings["max_retries"],
        error=str(job.get("error") or "") or None,
    )
    return {
        **job,
        "execution_meta": meta,
        "callback_freshness": freshness,
        "retry_truth": retry,
        "runner_mode": meta.get("runner_mode") or "embedded",
    }


def compose_external_execution_context(*, session_id: str = "default") -> str | None:
    presence = assess_external_runner_presence(session_id=session_id)
    if presence["runner_mode"] == "embedded":
        return None
    lines = [presence["summary"]]
    orphaned = detect_orphaned_jobs(session_id=session_id)
    if orphaned:
        job = orphaned[0]
        lines.append(
            describe_orphaned_execution(
                entity_name=str(job.get("entity_name") or "") or None,
                job_type=str(job.get("job_type") or "job"),
            )
        )
        return "\n\n".join(lines)
    for meta in list_execution_meta(session_id=session_id)[:3]:
        job = get_job(str(meta.get("job_id") or ""))
        if not job or job.get("status") in {"completed", "failed", "cancelled"}:
            continue
        if str(meta.get("dispatch_status") or "") == "awaiting_callback":
            lines.append(
                describe_awaiting_callback(
                    entity_name=str(job.get("entity_name") or "") or None,
                    job_type=str(job.get("job_type") or "job"),
                )
            )
            break
        retry = describe_retry_state(
            retries=int(job.get("retries") or 0),
            max_retries=trigger_settings()["max_retries"],
            error=str(job.get("error") or "") or None,
        )
        if retry.get("retrying"):
            lines.append(str(retry["phrase"]))
            break
    if len(lines) == 1 and presence["runner_mode"] == "degraded":
        return lines[0]
    return "\n\n".join(lines) if len(lines) > 1 else (lines[0] if lines else None)
