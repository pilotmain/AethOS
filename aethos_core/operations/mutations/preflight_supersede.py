# SPDX-License-Identifier: Apache-2.0
"""Mark older preflights superseded when a fresher match completes."""

from __future__ import annotations

from typing import Any

from aethos_core.operations.preflight_supersede import (
    _job_preflight_meta,
    _should_supersede,
    preflight_match_key,
)


def _mutation_job_meta(job: Any) -> tuple[str, str, str | None, str | None]:
    params = job.params or {}
    pf = params.get("mutation_preflight") or {}
    provider = str(params.get("provider") or pf.get("provider") or "unknown")
    operation_type = str(params.get("operation_type") or pf.get("operation_type") or job.job_type)
    target_raw = pf.get("target_name") or params.get("target_name") or params.get("preflight_target")
    target = str(target_raw).strip().lower() if target_raw else None
    target_status = str(pf.get("target_status") or params.get("target_status") or "")
    return provider, operation_type, target, target_status


def supersede_previous_mutation_preflights(*, new_job_id: str) -> list[str]:
    from aethos_core.runtime.job_types import uses_mutation_preflight
    from aethos_core.runtime.jobs import job_store

    new_job = job_store.get(new_job_id)
    if not new_job or not uses_mutation_preflight(new_job.job_type):
        return []

    new_provider, new_operation, new_target, _ = _mutation_job_meta(new_job)
    superseded: list[str] = []

    for job in job_store.list_all():
        if job.id == new_job_id or not uses_mutation_preflight(job.job_type):
            continue
        if job.params.get("is_current") is False:
            continue
        old_provider, old_operation, old_target, old_status = _mutation_job_meta(job)
        if not _should_supersede(
            old_provider=old_provider,
            old_operation=old_operation,
            old_target=old_target,
            old_target_status=old_status,
            new_provider=new_provider,
            new_operation=new_operation,
            new_target=new_target,
        ):
            continue
        job.params["is_current"] = False
        job.params["superseded_by"] = new_job_id
        job.params["preflight_status"] = "superseded"
        pf = job.params.get("mutation_preflight")
        if isinstance(pf, dict):
            pf["preflight_status"] = "superseded"
        superseded.append(job.id)

    new_job.params["is_current"] = True
    new_job.params["preflight_match_key"] = preflight_match_key(
        provider=new_provider,
        operation_type=new_operation,
        target_name=new_target,
    )
    if new_target:
        new_job.params["preflight_target"] = new_target
    return superseded
