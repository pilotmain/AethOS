# SPDX-License-Identifier: Apache-2.0
"""Mark older operation preflights superseded when a fresher match completes."""

from __future__ import annotations

from typing import Any


def _norm_target(name: str | None) -> str | None:
    if not name:
        return None
    return str(name).strip().lower() or None


def preflight_match_key(*, provider: str, operation_type: str, target_name: str | None) -> str:
    target = _norm_target(target_name) or "_unresolved_"
    return f"{provider}:{operation_type}:{target}"


def _job_preflight_meta(job: Any) -> tuple[str, str, str | None, str | None]:
    params = job.params or {}
    pf = params.get("operation_preflight") or {}
    provider = str(params.get("provider") or pf.get("provider") or "unknown")
    operation_type = str(params.get("operation_type") or pf.get("operation_type") or job.job_type)
    target = _norm_target(pf.get("target_name") or params.get("preflight_target"))
    target_status = str(pf.get("target_status") or params.get("preflight_target_status") or "")
    return provider, operation_type, target, target_status


def _should_supersede(
    *,
    old_provider: str,
    old_operation: str,
    old_target: str | None,
    old_target_status: str | None,
    new_provider: str,
    new_operation: str,
    new_target: str | None,
) -> bool:
    if old_provider != new_provider or old_operation != new_operation:
        return False
    if new_target and old_target and old_target == new_target:
        return True
    if new_target and (not old_target or old_target_status in ("missing", "ambiguous", "")):
        return True
    if not new_target and not old_target:
        return True
    return False


def supersede_previous_preflights(*, new_job_id: str) -> list[str]:
    """Mark older matching preflights superseded; return superseded job ids."""
    from aethos_core.runtime.job_types import uses_operation_preflight
    from aethos_core.runtime.jobs import job_store

    new_job = job_store.get(new_job_id)
    if not new_job or not uses_operation_preflight(new_job.job_type):
        return []

    new_provider, new_operation, new_target, _ = _job_preflight_meta(new_job)
    superseded: list[str] = []

    for job in job_store.list_all():
        if job.id == new_job_id or not uses_operation_preflight(job.job_type):
            continue
        if job.params.get("is_current") is False:
            continue
        old_provider, old_operation, old_target, old_status = _job_preflight_meta(job)
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
        pf = job.params.get("operation_preflight")
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
