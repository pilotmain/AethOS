# SPDX-License-Identifier: Apache-2.0
"""Mutation execution runtime — job dispatch + truth surfaces."""

from __future__ import annotations

from typing import Any


def get_mutation_job_truth(job_id: str) -> dict[str, Any]:
    from aethos_core.runtime.jobs import job_store

    job = job_store.get(job_id)
    if not job:
        return {"ok": False, "reason": "job_not_found", "job_id": job_id}

    artifact = dict(job.params.get("mutation_execution") or {})
    provider_result = artifact.get("provider_result") or {}
    railway_result = artifact.get("railway_mutation_result") or provider_result.get("railway_mutation_result")
    return {
        "ok": True,
        "job_id": job.id,
        "job_type": job.job_type,
        "status": job.status.value,
        "provider": job.params.get("provider"),
        "operation_type": job.params.get("operation_type"),
        "target_name": job.params.get("target_name"),
        "execution_state": job.params.get("execution_state") or artifact.get("execution_state"),
        "verification_state": job.params.get("verification_state") or artifact.get("verification_state"),
        "lifecycle_state": job.params.get("lifecycle_state") or artifact.get("lifecycle_state"),
        "canonical_lifecycle_state": job.params.get("canonical_lifecycle_state") or artifact.get("canonical_lifecycle_state"),
        "executed": job.params.get("executed"),
        "provider_mutation_requested": job.params.get("provider_mutation_requested") or artifact.get("provider_mutation_requested"),
        "verification_job_id": job.params.get("verification_job_id") or artifact.get("verification_job_id"),
        "provider_result": provider_result,
        "railway_mutation_result": railway_result,
        "restart_verification_state": job.params.get("restart_verification_state"),
        "restart_provider_request": job.params.get("restart_provider_request"),
        "restart_transition": job.params.get("restart_transition"),
        "restart_service_health": job.params.get("restart_service_health"),
        "restart_final_verification": job.params.get("restart_final_verification"),
        "railway_before_snapshot": job.params.get("railway_before_snapshot"),
        "railway_after_snapshot": job.params.get("railway_after_snapshot"),
        "failure_type": job.params.get("failure_type") or artifact.get("failure_type"),
        "failure_classification": job.params.get("failure_classification") or artifact.get("failure_classification"),
        "audit": job.params.get("audit") or artifact.get("audit"),
        "summary": job.result_summary or job.result,
    }


def get_mutation_job_audit(job_id: str) -> dict[str, Any]:
    truth = get_mutation_job_truth(job_id)
    if not truth.get("ok"):
        return truth
    audit = truth.get("audit")
    if not isinstance(audit, dict):
        return {"ok": False, "reason": "audit_not_found", "job_id": job_id}
    return {"ok": True, "job_id": job_id, "audit": audit}


def get_mutation_job_verification(job_id: str) -> dict[str, Any]:
    from aethos_core.runtime.jobs import job_store

    truth = get_mutation_job_truth(job_id)
    if not truth.get("ok"):
        return truth
    verify_id = truth.get("verification_job_id")
    if not verify_id:
        return {
            "ok": True,
            "job_id": job_id,
            "verification_job_id": None,
            "verification_state": truth.get("verification_state"),
            "summary": "Verification has not been scheduled yet.",
        }
    verify_job = job_store.get(str(verify_id))
    return {
        "ok": True,
        "job_id": job_id,
        "verification_job_id": verify_id,
        "verification_state": truth.get("verification_state"),
        "verification_job": verify_job.to_dict() if verify_job else None,
    }


def execute_mutation_job(job_id: str) -> dict[str, Any]:
    from aethos_core.operations.mutations.execution import run_mutation_execution
    from aethos_core.operations.mutations.lifecycle_authority import sync_mutation_job_lifecycle
    from aethos_core.runtime.jobs import job_store

    job = job_store.get(job_id)
    if not job:
        return {"ok": False, "reason": "job_not_found", "job_id": job_id}
    if job.job_type != "mutation_execution":
        return {"ok": False, "reason": "not_mutation_execution", "job_id": job_id}
    if job.status.value not in {"queued", "running"}:
        return {"ok": False, "reason": "job_not_runnable", "job_id": job_id, "status": job.status.value}

    job_store.begin_running(job_id)
    outcome = run_mutation_execution(params=job.params, job_id=job_id)
    job = job_store.get(job_id)
    if job:
        job.params["mutation_execution"] = outcome.artifact
        job.params["dry_run"] = outcome.dry_run
        job.params["mutating"] = outcome.executed
        job.params["executed"] = outcome.executed
        job.params["provider_mutation_requested"] = outcome.artifact.get("provider_mutation_requested")
        job.params["execution_state"] = outcome.artifact.get("execution_state")
        job.params["lifecycle_state"] = outcome.artifact.get("lifecycle_state")
        job.params["verification_state"] = outcome.artifact.get("verification_state")
        job.params["audit"] = outcome.artifact.get("audit")
        if outcome.artifact.get("verification_job_id"):
            job.params["verification_job_id"] = outcome.artifact["verification_job_id"]
        sync_mutation_job_lifecycle(job)
        job_store.complete_with_result(
            job_id,
            full_result=outcome.full_result,
            summary=str(job.params.get("lifecycle_summary") or outcome.summary),
            preview=outcome.summary[:240],
            provider="mutation_execution",
            model="deterministic",
            used_llm=False,
            fallback=False,
        )
    return get_mutation_job_truth(job_id)
