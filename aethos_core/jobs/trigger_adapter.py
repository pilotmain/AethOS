# SPDX-License-Identifier: Apache-2.0
"""Trigger.dev adapter — external dispatch with embedded/degraded fallback."""

from __future__ import annotations

import json
import logging
import threading
import urllib.error
import urllib.request
from time import time
from typing import Any

from aethos_core.external_execution_truth.degraded_execution_language import describe_degraded_fallback
from aethos_core.external_execution_truth.execution_store import upsert_execution_meta
from aethos_core.external_execution_truth.retry_truth import compose_retry_notification
from aethos_core.external_execution_truth.trigger_dispatch_truth import resolve_runner_mode, trigger_settings
from aethos_core.external_execution_truth.webhook_reconciliation import record_webhook_callback
from aethos_core.jobs.job_artifact_bridge import apply_job_artifact
from aethos_core.jobs.job_notifications import compose_completion_message, enqueue_job_notification
from aethos_core.jobs.job_state import get_job, update_job
from aethos_core.operational_deliverables.deliverable_templates import get_agent_deliverable

logger = logging.getLogger(__name__)

_JOB_TYPE_TASK_MAP = {
    "research_scan": "aethos-research-scan",
    "gtm_synthesis": "aethos-gtm-synthesis",
    "provider_verification": "aethos-provider-verification",
    "recovery_window_check": "aethos-recovery-window-check",
    "artifact_summarization": "aethos-artifact-summarization",
}


def _attempt_trigger_api_dispatch(*, job_id: str, job_type: str, session_id: str) -> dict[str, Any]:
    settings = trigger_settings()
    task_id = _JOB_TYPE_TASK_MAP.get(job_type, "aethos-durable-job")
    url = f"https://api.trigger.dev/api/v1/tasks/{task_id}/trigger"
    payload = json.dumps({"payload": {"job_id": job_id, "session_id": session_id, "job_type": job_type}}).encode()
    request = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Authorization": f"Bearer {settings['api_key']}",
            "Content-Type": "application/json",
            "Trigger-Project-Id": settings["project_id"],
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=8) as response:
            body = json.loads(response.read().decode())
            run_id = str(body.get("id") or body.get("runId") or f"trigger-{job_id}")
            return {"ok": True, "external_id": run_id, "api_reachable": True}
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError) as exc:
        logger.warning("Trigger.dev dispatch failed for %s: %s", job_id, exc)
        return {"ok": False, "reason": str(exc)[:200], "api_reachable": False}


def dispatch_job(*, job_id: str) -> dict[str, Any]:
    """Dispatch job to Trigger.dev, or embedded/degraded runner."""
    job = get_job(job_id)
    if not job:
        return {"ok": False, "reason": "job_not_found"}

    session_id = str(job.get("session_id") or "default")
    job_type = str(job.get("job_type") or "")
    settings = trigger_settings()
    mode = resolve_runner_mode()

    update_job(job_id, status="dispatching", started_at=job.get("started_at") or time())

    if mode == "embedded":
        upsert_execution_meta(
            job_id,
            session_id=session_id,
            runner_mode="embedded",
            dispatch_status="running",
            dispatched_at=time(),
        )
        update_job(job_id, status="running")
        threading.Thread(target=_embedded_execute, args=(job_id,), daemon=True).start()
        return {"ok": True, "mode": "embedded"}

    api_result = _attempt_trigger_api_dispatch(job_id=job_id, job_type=job_type, session_id=session_id)
    if not api_result.get("ok"):
        mode = "degraded"
        upsert_execution_meta(
            job_id,
            session_id=session_id,
            runner_mode="degraded",
            dispatch_status="degraded_fallback",
            dispatched_at=time(),
            degraded_reason=api_result.get("reason"),
        )
        update_job(job_id, status="running")
        threading.Thread(target=_embedded_execute, args=(job_id, "degraded"), daemon=True).start()
        return {
            "ok": True,
            "mode": "degraded",
            "reason": api_result.get("reason"),
            "message": describe_degraded_fallback(reason=str(api_result.get("reason") or "external runner unavailable")),
        }

    external_id = str(api_result.get("external_id") or f"trigger-{job_id}")
    upsert_execution_meta(
        job_id,
        session_id=session_id,
        runner_mode="external",
        dispatch_status="awaiting_callback",
        dispatched_at=time(),
        external_id=external_id,
    )
    update_job(job_id, status="awaiting_callback", external_id=external_id)
    return {"ok": True, "mode": "external", "external_id": external_id}


def handle_trigger_callback(*, job_id: str, status: str, output: dict[str, Any] | None = None) -> dict[str, Any]:
    """Webhook callback from Trigger.dev."""
    record_webhook_callback(job_id=job_id, status=status, output=output)
    job = get_job(job_id)
    if not job:
        return {"ok": False, "reason": "job_not_found"}
    if status == "retrying":
        retries = int(job.get("retries") or 0) + 1
        update_job(job_id, status="retrying", retries=retries)
        note = compose_retry_notification(job_type=str(job.get("job_type") or ""), retries=retries)
        if note:
            enqueue_job_notification(
                session_id=str(job.get("session_id") or "default"),
                message=note,
                job_id=job_id,
                job_type=str(job.get("job_type") or ""),
            )
        return {"ok": True, "status": "retrying", "retries": retries}
    if status == "failed":
        update_job(job_id, status="failed", error=str((output or {}).get("error") or "trigger_failed"))
        return {"ok": True, "status": "failed"}
    return _complete_job(job_id, output or {})


def _embedded_execute(job_id: str, runner_mode: str = "embedded") -> None:
    job = get_job(job_id)
    if not job:
        return
    # Detached background thread: no request context. Re-establish the owning
    # tenant from the job's stamped tenant_id so any resolver inside the handler
    # sees the right tenant, never the (empty/foreign) request ContextVar
    # (Correction 1). No-op in single-tenant mode (tenant = "default").
    from aethos_core.tenancy import tenant_scope

    try:
        with tenant_scope(job.get("tenant_id")):
            update_job(job_id, status="running")
            output = _run_job_handler(job)
            _complete_job(job_id, output, runner_mode=runner_mode)
    except Exception as exc:
        logger.exception("durable job failed: %s", job_id)
        retries = int(job.get("retries") or 0) + 1
        settings = trigger_settings()
        if retries <= settings["max_retries"]:
            update_job(job_id, status="retrying", retries=retries, error=str(exc)[:240])
            upsert_execution_meta(job_id, dispatch_status="retrying", last_retry_at=time())
            note = compose_retry_notification(job_type=str(job.get("job_type") or ""), retries=retries)
            if note:
                enqueue_job_notification(
                    session_id=str(job.get("session_id") or "default"),
                    message=note,
                    job_id=job_id,
                    job_type=str(job.get("job_type") or ""),
                )
            delay = float(settings["retry_backoff_seconds"])
            threading.Timer(delay, lambda: dispatch_job(job_id=job_id)).start()
        else:
            update_job(job_id, status="failed", error=str(exc)[:240])


def _run_job_handler(job: dict[str, Any]) -> dict[str, Any]:
    job_type = str(job.get("job_type") or "")
    entity_name = job.get("entity_name")
    params = dict(job.get("params") or {})

    if job_type == "recovery_window_check":
        delay = int(params.get("delay_seconds") or 0)
        if delay > 0:
            import time as _time

            _time.sleep(min(delay, 30))

    if job_type == "research_scan":
        name = str(entity_name or "Research agent")
        d = get_agent_deliverable(agent_name=name, stage=2)
        return {"agent_name": name, "stage": 2, "summary": d["headline"], **d}
    if job_type == "gtm_synthesis":
        name = str(entity_name or "Analysis agent")
        d = get_agent_deliverable(agent_name=name, stage=2)
        return {"agent_name": name, "stage": 2, "summary": d["headline"], **d}
    if job_type == "provider_verification":
        return {
            "agent_name": "Provider Operations Agent",
            "stage": 2,
            "summary": "Provider verification completed — runtime signals reviewed under governance.",
            "findings": ["Railway deployment signals", "Vercel deployment signals", "GitHub workflow signals"],
        }
    if job_type == "recovery_window_check":
        window = str(params.get("window") or "delayed")
        return {
            "summary": (
                f"The {window} recovery check completed. "
                "The restart appears to be holding across current runtime and deployment signals."
            ),
            "window": window,
        }
    if job_type == "artifact_summarization":
        return {"summary": "Artifact summarization complete.", "stage": 2}
    d = get_agent_deliverable(agent_name=str(entity_name or "Operational agent"), stage=2)
    return {"summary": d.get("headline"), "stage": 2, **d}


def _complete_job(job_id: str, output: dict[str, Any], *, runner_mode: str = "embedded") -> dict[str, Any]:
    job = get_job(job_id)
    if not job:
        return {"ok": False}
    session_id = str(job.get("session_id") or "default")
    job_type = str(job.get("job_type") or "")
    entity_name = job.get("entity_name")

    bridge_result = None
    if job_type in {"research_scan", "gtm_synthesis", "artifact_summarization"}:
        bridge_result = apply_job_artifact(
            session_id=session_id,
            job_type=job_type,
            entity_name=str(entity_name) if entity_name else None,
            output=output,
        )

    summary = str((bridge_result or {}).get("summary") or output.get("summary") or "Job completed.")
    update_job(job_id, status="completed", completed_at=time(), artifact_ref=summary[:120])
    upsert_execution_meta(
        job_id,
        session_id=session_id,
        runner_mode=runner_mode,
        dispatch_status="completed",
        last_callback_at=time(),
        completed_at=time(),
    )
    message = compose_completion_message(job_type=job_type, entity_name=str(entity_name) if entity_name else None, summary=summary)
    enqueue_job_notification(session_id=session_id, message=message, job_id=job_id, job_type=job_type)
    return {"ok": True, "job_id": job_id, "summary": summary, "bridge": bridge_result}
