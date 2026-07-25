# SPDX-License-Identifier: Apache-2.0
"""Tool execution loop — call tool, capture output, collect evidence."""

from __future__ import annotations

from typing import Any

from aethos_core.operational_skill_runtime.evidence_collector import build_universal_evidence_from_job
from aethos_core.provider_skills.runtime import execute_provider_operation


def execute_operation_loop(
    *,
    provider: str,
    operation: str,
    target: Any,
    approved: bool,
    job_id: str | None = None,
    before_snapshot: dict[str, Any] | None = None,
    approved_at: str | None = None,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Run provider skill execute → collect_evidence → verify and return universal bundle."""
    payload = execute_provider_operation(
        provider=provider,
        operation=operation,
        target=target,
        approved=approved,
        job_id=job_id,
        before_snapshot=before_snapshot,
        approved_at=approved_at,
        request_id=request_id,
    )
    if job_id:
        from aethos_core.runtime.jobs import job_store

        job = job_store.get(job_id)
        if job is not None:
            params = dict(getattr(job, "params", None) or {})
            bundle = payload.get("evidence_bundle") or {}
            if bundle.get("command_submitted"):
                params["restart_command_submitted"] = True
                params["command"] = bundle.get("command") or payload.get("command")
            job.params = params
            universal = build_universal_evidence_from_job(job)
            payload["universal_evidence"] = universal.to_dict()
    return payload
