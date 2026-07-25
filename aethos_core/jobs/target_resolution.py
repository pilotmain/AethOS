# SPDX-License-Identifier: Apache-2.0
"""Resolve targets on existing mutation preflight jobs."""

from __future__ import annotations

from typing import Any

from aethos_core.providers.railway.target_resolver import (
    TARGET_APPROVAL_THRESHOLD,
    list_railway_target_candidates,
    resolve_railway_provider_target,
)


def _apply_preflight_outcome(*, job_id: str) -> dict[str, Any]:
    from aethos_core.jobs.job_approval_guidance import build_mutation_approval_metadata
    from aethos_core.operations.mutations.preflight import run_mutation_preflight
    from aethos_core.runtime.jobs import job_store

    job = job_store.get(job_id)
    if not job:
        return {"ok": False, "reason": "job_not_found"}

    outcome = run_mutation_preflight(job_type=job.job_type, params=job.params)
    job.params["mutation_preflight"] = outcome.to_dict()
    job.params["mutation_execution_enabled"] = outcome.mutation_execution_enabled
    job.params["preflight_status"] = outcome.preflight_status
    job.params["risk_tier"] = outcome.risk_tier.value
    job.params["blast_radius"] = outcome.blast_radius
    job.params["rollback_plan"] = outcome.rollback_plan
    job.params["read_only"] = False
    job.params["mutating"] = True
    job.params["execution_blocked"] = outcome.preflight_status != "ready_for_mutation_approval"
    job.params["is_current"] = True
    job.params["target_resolved"] = outcome.target_resolved
    if outcome.target:
        job.params["target"] = outcome.target
    job.params.update(build_mutation_approval_metadata(preflight_status=outcome.preflight_status))
    if outcome.workflow_resolution:
        job.params["workflow_resolution"] = outcome.workflow_resolution
    if outcome.workflow_resolution_debug:
        job.params["workflow_resolution_debug"] = outcome.workflow_resolution_debug
    if outcome.discovery_failure_reason:
        job.params["discovery_failure_reason"] = outcome.discovery_failure_reason

    job_store.complete_with_result(
        job_id,
        full_result=outcome.full_result,
        summary=outcome.summary,
        preview=outcome.summary[:240],
        provider="mutation_preflight",
        model="deterministic",
        used_llm=False,
        fallback=False,
    )
    return {
        "ok": True,
        "job_id": job_id,
        "preflight_status": outcome.preflight_status,
        "target_resolved": outcome.target_resolved,
        "target": outcome.target,
    }


def resolve_target_on_job(*, job_id: str, service_name: str) -> dict[str, Any]:
    from aethos_core.runtime.jobs import job_store

    job = job_store.get(job_id)
    if not job:
        return {"ok": False, "reason": "job_not_found"}
    if job.job_type != "mutation_preflight":
        return {"ok": False, "reason": "not_mutation_preflight"}

    target = resolve_railway_provider_target(
        user_request=f"Railway {service_name}",
        operation_type=str(job.params.get("operation_type") or "restart"),
    )
    if not target.resolved or target.confidence < TARGET_APPROVAL_THRESHOLD:
        return {
            "ok": False,
            "reason": "target_unresolved",
            "target": target.to_dict(),
            "candidates": target.candidates,
        }

    job.params["target_name"] = target.service_name
    job.params["target"] = target.to_dict()
    job.params["target_resolved"] = True
    job.params["target_status"] = "resolved"
    result = _apply_preflight_outcome(job_id=job_id)
    result["target"] = target.to_dict()
    return result


def refresh_railway_targets(*, limit: int = 20) -> dict[str, Any]:
    candidates = list_railway_target_candidates(limit=limit)
    return {"ok": True, "candidates": candidates, "count": len(candidates)}


def refresh_job_target_candidates(*, job_id: str, limit: int = 20) -> dict[str, Any]:
    from aethos_core.runtime.jobs import job_store

    job = job_store.get(job_id)
    if not job:
        return {"ok": False, "reason": "job_not_found"}
    refreshed = refresh_railway_targets(limit=limit)
    refreshed["job_id"] = job_id
    return refreshed
