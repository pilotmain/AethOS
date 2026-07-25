# SPDX-License-Identifier: Apache-2.0
"""External execution truth API — Phase 11.8.1."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(tags=["external-execution"])


class TriggerWebhookIn(BaseModel):
    job_id: str
    status: str = "completed"
    output: dict[str, Any] = Field(default_factory=dict)
    delivery_id: str | None = None
    sequence: int | None = None
    signature: str | None = None


@router.get("/external-execution/state")
def get_external_execution_state_api(session_id: str = "default") -> dict[str, Any]:
    from aethos_core.external_execution_truth.runtime import assess_external_execution_runtime

    return assess_external_execution_runtime(session_id=session_id, channel="api")


@router.get("/external-execution/freshness")
def get_external_execution_freshness_api(session_id: str = "default") -> dict[str, Any]:
    from aethos_core.external_execution_truth.execution_store import list_execution_meta
    from aethos_core.external_execution_truth.runtime_truth_bridge import enrich_job_with_execution_truth
    from aethos_core.jobs.job_state import list_jobs

    jobs = [enrich_job_with_execution_truth(j) for j in list_jobs(session_id=session_id, limit=20)]
    return {"ok": True, "session_id": session_id, "jobs": jobs, "meta_count": len(list_execution_meta(session_id=session_id))}


@router.get("/external-execution/retries")
def get_external_execution_retries_api(session_id: str = "default") -> dict[str, Any]:
    from aethos_core.jobs.job_state import list_jobs

    retrying = [j for j in list_jobs(session_id=session_id, limit=50) if j.get("status") == "retrying"]
    return {"ok": True, "retrying_jobs": retrying, "count": len(retrying)}


@router.get("/external-execution/orphaned")
def get_external_execution_orphaned_api(session_id: str = "default") -> dict[str, Any]:
    from aethos_core.external_execution_truth.orphaned_job_detection import detect_orphaned_jobs

    orphaned = detect_orphaned_jobs(session_id=session_id)
    return {"ok": True, "orphaned_jobs": orphaned, "count": len(orphaned)}


@router.get("/external-execution/divergence")
def get_external_execution_divergence_api(session_id: str = "default") -> dict[str, Any]:
    from aethos_core.external_execution_truth.execution_divergence import assess_execution_divergence
    from aethos_core.jobs.job_state import list_jobs

    rows = [
        assess_execution_divergence(job_id=str(j.get("job_id") or ""))
        for j in list_jobs(session_id=session_id, limit=20)
    ]
    return {"ok": True, "divergences": rows}


@router.post("/external-execution/webhook/trigger")
def post_external_trigger_webhook(
    body: TriggerWebhookIn,
    x_aethos_signature: str | None = Header(default=None, alias="X-Aethos-Signature"),
) -> dict[str, Any]:
    from aethos_core.jobs.job_runtime import process_trigger_callback

    payload = body.model_dump()
    if x_aethos_signature and not payload.get("signature"):
        payload["signature"] = x_aethos_signature
    result = process_trigger_callback(payload)
    if not result.get("ok") and result.get("reason") == "job_not_found":
        raise HTTPException(status_code=404, detail="Durable job not found")
    if not result.get("ok") and result.get("reason") in {
        "missing_signature",
        "invalid_signature",
        "stale_callback_sequence",
    }:
        raise HTTPException(status_code=401 if "signature" in str(result.get("reason")) else 409, detail=result)
    return result
