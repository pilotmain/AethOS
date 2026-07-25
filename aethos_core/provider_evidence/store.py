# SPDX-License-Identifier: Apache-2.0
"""Provider evidence persistence — job-linked evidence bundles."""

from __future__ import annotations

from typing import Any


def attach_evidence_bundle(*, job_id: str, bundle: dict[str, Any]) -> dict[str, Any]:
    from aethos_core.runtime.jobs import job_store

    job = job_store.get(job_id)
    if not job:
        return {"ok": False, "error": "job_not_found", "job_id": job_id}
    job.params["provider_evidence_bundle"] = dict(bundle)
    exec_artifact = job.params.get("mutation_execution")
    if isinstance(exec_artifact, dict):
        exec_artifact = dict(exec_artifact)
        exec_artifact["provider_evidence_bundle"] = dict(bundle)
        job.params["mutation_execution"] = exec_artifact
    return {"ok": True, "job_id": job_id, "bundle": bundle}


def get_evidence_bundle(*, job_id: str) -> dict[str, Any]:
    from aethos_core.runtime.jobs import job_store

    job = job_store.get(job_id)
    if not job:
        return {"ok": False, "error": "job_not_found", "job_id": job_id}
    bundle = job.params.get("provider_evidence_bundle")
    if not isinstance(bundle, dict):
        exec_artifact = job.params.get("mutation_execution") or {}
        if isinstance(exec_artifact, dict):
            bundle = exec_artifact.get("provider_evidence_bundle")
    if not isinstance(bundle, dict):
        bundle = _bundle_from_job_params(job.params)
    if not bundle:
        return {"ok": False, "error": "evidence_not_found", "job_id": job_id}
    return {"ok": True, "job_id": job_id, "bundle": bundle}


def _bundle_from_job_params(params: dict[str, Any]) -> dict[str, Any] | None:
    provider = str(params.get("provider") or "")
    if provider != "railway":
        return None
    exec_artifact = params.get("mutation_execution") or {}
    if not isinstance(exec_artifact, dict):
        exec_artifact = {}
    proof = exec_artifact.get("railway_execution_proof") or {}
    if not isinstance(proof, dict):
        proof = {}
    if not params.get("restart_command_submitted") and not proof.get("restart_command_submitted"):
        if params.get("executed") is not True and exec_artifact.get("executed") is not True:
            return None
    return {
        "operation": str(params.get("operation_type") or exec_artifact.get("operation_type") or "restart"),
        "provider": "railway",
        "target": str(params.get("target_name") or exec_artifact.get("target_name") or ""),
        "approved_at": params.get("mutation_execution_approved_at_iso"),
        "command": proof.get("command") or exec_artifact.get("command"),
        "command_submitted": bool(
            params.get("restart_command_submitted")
            or proof.get("restart_command_submitted")
            or exec_artifact.get("restart_command_submitted")
        ),
        "execution_mode": proof.get("execution_mode") or exec_artifact.get("execution_mode"),
        "provider_response": proof.get("railway_response") or exec_artifact.get("provider_result") or {},
        "before": params.get("railway_before_snapshot") or {},
        "after": params.get("railway_after_snapshot") or {},
        "evidence": {
            "deployment_transition_detected": params.get("restart_transition") == "detected",
            "log_activity_after_approval": _log_activity(params),
            "health_confirmed": params.get("restart_service_health") == "online",
            "runtime_errors_detected": bool(params.get("runtime_errors_detected")),
            "restart_command_submitted": bool(params.get("restart_command_submitted")),
            "transition_proof": params.get("restart_transition_proof"),
        },
        "verification": {
            "status": params.get("restart_verification_state") or params.get("verification_state"),
            "confidence": "bounded",
            "reason": str(params.get("restart_final_verification") or ""),
            "verified": bool(params.get("verified")),
        },
        "diagnosis": params.get("provider_diagnosis"),
        "fix_plan": params.get("provider_fix_plan"),
    }


def _log_activity(params: dict[str, Any]) -> bool:
    state = str(params.get("restart_verification_state") or "")
    if state == "log_restart_detected":
        return True
    proof = params.get("restart_transition_proof")
    return proof == "logs"
