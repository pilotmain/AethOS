# SPDX-License-Identifier: Apache-2.0
"""Embedded vs external execution divergence — Phase 11.8.1."""

from __future__ import annotations

from typing import Any

from aethos_core.external_execution_truth.execution_store import get_execution_meta
from aethos_core.jobs.job_state import get_job


def assess_execution_divergence(*, job_id: str) -> dict[str, Any]:
    job = get_job(job_id)
    meta = get_execution_meta(job_id)
    if not job or not meta:
        return {"ok": False, "divergent": False, "reason": "insufficient_data"}
    runner_mode = str(meta.get("runner_mode") or "embedded")
    job_status = str(job.get("status") or "")
    dispatch_status = str(meta.get("dispatch_status") or "")
    divergent = False
    reasons: list[str] = []
    if runner_mode == "external" and job_status == "completed" and not meta.get("last_callback_at"):
        divergent = True
        reasons.append("completed_without_callback")
    if dispatch_status == "awaiting_callback" and job_status == "completed":
        divergent = True
        reasons.append("awaiting_callback_but_completed")
    if meta.get("orphaned") and job_status not in {"orphaned", "failed"}:
        divergent = True
        reasons.append("orphaned_meta_mismatch")
    return {
        "ok": True,
        "job_id": job_id,
        "divergent": divergent,
        "reasons": reasons,
        "runner_mode": runner_mode,
        "job_status": job_status,
        "dispatch_status": dispatch_status,
    }
