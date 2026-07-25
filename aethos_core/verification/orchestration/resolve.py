# SPDX-License-Identifier: Apache-2.0
"""Evaluate readonly verification and resolve mutation lifecycle."""

from __future__ import annotations

from time import time
from typing import Any

from aethos_core.operations.mutations.failures import VERIFICATION_FAILED, VERIFICATION_TIMEOUT
from aethos_core.operations.mutations.lifecycle import lifecycle_after_verification
from aethos_core.operations.mutations.lifecycle_authority import sync_mutation_job_lifecycle
from aethos_core.verification.artifact import build_verification_artifact


def _railway_verification_evidence(
    readonly_artifact: dict[str, Any],
    *,
    source_exec: dict[str, Any],
    mutation_params: dict[str, Any] | None = None,
) -> tuple[str, dict[str, Any]]:
    from aethos_core.providers.railway.hardening.restart_transition import (
        LOG_RESTART_DETECTED,
        RESTART_TRANSITION_DETECTED,
        RESTART_UNVERIFIED,
        SERVICE_ONLINE_BUT_RESTART_UNPROVEN,
        STABILIZING,
        VERIFICATION_FAILED,
        verify_railway_restart_transition,
    )

    provider_result = source_exec.get("provider_result") or {}
    if not isinstance(provider_result, dict):
        provider_result = {}
    rollback_meta = source_exec.get("rollback_metadata") or provider_result.get("rollback_metadata") or {}
    if not isinstance(rollback_meta, dict):
        rollback_meta = {}

    mutation_params = mutation_params or {}
    before_snapshot = (
        mutation_params.get("railway_before_snapshot")
        or source_exec.get("railway_before_snapshot")
        or rollback_meta.get("deployment_snapshot_before")
    )
    approved_at = (
        mutation_params.get("mutation_execution_approved_at_iso")
        or source_exec.get("mutation_execution_approved_at_iso")
        or rollback_meta.get("approved_at")
    )
    target_payload = mutation_params.get("target")
    target_service_id = target_payload.get("service_id") if isinstance(target_payload, dict) else None
    service_id = str(
        provider_result.get("service_id")
        or rollback_meta.get("service_id")
        or (before_snapshot or {}).get("service_id")
        or target_service_id
        or ""
    )

    if isinstance(before_snapshot, dict) and service_id:
        restart = verify_railway_restart_transition(
            service_id=service_id,
            before_snapshot=before_snapshot,
            approved_at=approved_at,
            provider_result=provider_result,
            readonly_artifact=readonly_artifact,
            provider_request_accepted=bool(
                provider_result.get("restart_command_submitted")
                if provider_result.get("restart_command_submitted") is not None
                else provider_result.get("ok") or source_exec.get("provider_mutation_requested")
            ),
        )
        restart_dict = restart.to_dict()
        state = restart.state
        if state in {RESTART_TRANSITION_DETECTED, LOG_RESTART_DETECTED} and restart.verified:
            verification_result = "healthy"
        elif state in {RESTART_UNVERIFIED, SERVICE_ONLINE_BUT_RESTART_UNPROVEN}:
            verification_result = "inconclusive"
        elif state in {STABILIZING, "restart_requested"}:
            verification_result = "pending"
        elif state == VERIFICATION_FAILED:
            verification_result = "unhealthy"
        else:
            verification_result = "inconclusive"
        extra = {
            **restart_dict,
            "restart_verification_state": state,
            "restart_command_submitted": restart.restart_command_submitted,
            "transition_proof": restart.transition_proof,
            "deployment_state_before": (before_snapshot or {}).get("latest_deployment_status"),
            "deployment_state_after": (restart_dict.get("after_snapshot") or {}).get("latest_deployment_status"),
            "deployment_id": rollback_meta.get("deployment_id") or provider_result.get("deployment_id"),
            "readonly_summary": readonly_artifact.get("summary"),
        }
        return verification_result, extra

    evidence = readonly_artifact.get("evidence") or readonly_artifact.get("items") or []
    deployment_state = None
    if isinstance(evidence, list):
        for item in evidence:
            if isinstance(item, dict):
                deployment_state = item.get("state") or item.get("status")
                if deployment_state:
                    break

    extra = {
        "deployment_state": deployment_state,
        "deployment_state_before": rollback_meta.get("deployment_state_before"),
        "deployment_state_after": rollback_meta.get("deployment_state_after") or provider_result.get("deployment_state_after"),
        "restart_timestamp": rollback_meta.get("restart_timestamp") or provider_result.get("restart_timestamp"),
        "deployment_id": rollback_meta.get("deployment_id") or provider_result.get("deployment_id"),
        "readonly_summary": readonly_artifact.get("summary"),
        "restart_verification_state": "restart_unverified",
        "provider_request": "unknown",
        "restart_transition": "not_detected",
        "service_health": "unknown",
        "final_verification": "unverified",
    }

    state_str = str(deployment_state or extra.get("deployment_state_after") or "").lower()
    summary = str(readonly_artifact.get("summary") or "").lower()
    service_online = state_str in ("success", "running", "ready", "active") or any(
        w in summary for w in ("success", "running", "healthy", "active")
    )
    extra["service_health"] = "online" if service_online else "unknown"
    if service_online:
        extra["restart_verification_state"] = SERVICE_ONLINE_BUT_RESTART_UNPROVEN
        return "inconclusive", extra
    return "pending", extra


def _vercel_verification_evidence(readonly_artifact: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    summary = str(readonly_artifact.get("summary") or "").lower()
    extra = {"readonly_summary": readonly_artifact.get("summary"), "deployment_alias": None, "deployment_state": None}
    if any(w in summary for w in ("ready", "success", "active", "production")):
        return "healthy", extra
    if any(w in summary for w in ("failed", "error", "canceled")):
        return "unhealthy", extra
    return "pending", extra


def resolve_mutation_verification(*, verification_job_id: str) -> dict[str, Any] | None:
    from aethos_core.runtime.jobs import job_store

    vjob = job_store.get(verification_job_id)
    if not vjob:
        return None
    mutation_id = str(vjob.params.get("verification_of_mutation_job_id") or "")
    if not mutation_id:
        return None
    mjob = job_store.get(mutation_id)
    if not mjob:
        return None

    source_exec = vjob.params.get("source_mutation_execution") or {}
    if not isinstance(source_exec, dict):
        source_exec = {}
    provider = str(mjob.params.get("provider") or source_exec.get("provider") or "unknown")
    mutation_op = str(source_exec.get("operation_type") or mjob.params.get("operation_type") or "")
    target = mjob.params.get("target_name")
    readonly_artifact = vjob.params.get("readonly_execution") or {}
    if not isinstance(readonly_artifact, dict):
        readonly_artifact = {}

    verification_result = "unknown"
    failure_type = None
    failure_classification = None
    retry_history: list[dict[str, Any]] = []
    extra: dict[str, Any] = {}

    if provider == "github" and mutation_op == "workflow_rerun":
        from aethos_core.operations.mutations.failures import RUN_NOT_DETECTED
        from aethos_core.providers.github.auth import GitHubAuthAdapter
        from aethos_core.providers.github.mutations.workflow_rerun_verification import verify_workflow_rerun

        provider_result = source_exec.get("provider_result") or {}
        if not isinstance(provider_result, dict):
            provider_result = {}
        credential_id = str(mjob.params.get("credential_id") or "")
        token = GitHubAuthAdapter().get_api_token(credential_id) if credential_id else ""
        repo = str(target or provider_result.get("repository") or "")
        if token and repo:
            polled = verify_workflow_rerun(
                token,
                repository=repo,
                source_run_id=provider_result.get("source_run_id"),
                workflow_id=provider_result.get("workflow_id"),
                source_created_at=provider_result.get("source_created_at"),
                source_run_number=provider_result.get("source_run_number"),
                session_id=str(mjob.session_id or "default"),
            )
            retry_history = list(polled.get("retries") or [])
            extra = {k: v for k, v in polled.items() if k not in ("ok", "retries")}
            if polled.get("ok"):
                verification_result = str(polled.get("verification_result") or "pending")
            else:
                verification_result = "unhealthy"
                failure_type = polled.get("failure_type") or RUN_NOT_DETECTED
                failure_classification = polled.get("failure_classification") or failure_type
                if failure_classification == RUN_NOT_DETECTED and polled.get("verification_attempts", 0) >= 5:
                    failure_classification = VERIFICATION_TIMEOUT
            if token and repo and polled.get("new_run_detected"):
                from aethos_core.providers.github.mutations.workflow_rerun_verification import (
                    update_correlation_after_rerun_verification,
                )

                chain_update = update_correlation_after_rerun_verification(
                    session_id=str(mjob.session_id or "default"),
                    repository=repo,
                    verification=polled,
                )
                extra["deployment_chain"] = chain_update.get("deployment_chain") or polled.get("deployment_chain")
                extra["rerun_outcome"] = polled.get("rerun_outcome")
                extra["chain_summary"] = polled.get("chain_summary")
                extra["chain_verdict"] = polled.get("chain_verdict")
                extra["proactive_verification_reply"] = (
                    chain_update.get("proactive_verification_reply") or polled.get("proactive_verification_reply")
                )
                if extra.get("proactive_verification_reply"):
                    extra["chain_summary"] = extra["proactive_verification_reply"]
        else:
            verification_result = "unhealthy"
            failure_type = VERIFICATION_FAILED
            failure_classification = VERIFICATION_FAILED
    elif provider == "railway" and mutation_op in ("restart", "redeploy"):
        verification_result, extra = _railway_verification_evidence(
            readonly_artifact,
            source_exec=source_exec,
            mutation_params=mjob.params,
        )
        if verification_result == "unhealthy":
            failure_type = VERIFICATION_FAILED
            failure_classification = VERIFICATION_FAILED
    elif provider == "vercel" and mutation_op in ("redeploy", "restart"):
        verification_result, extra = _vercel_verification_evidence(readonly_artifact)
        if verification_result == "unhealthy":
            failure_type = VERIFICATION_FAILED
            failure_classification = VERIFICATION_FAILED
    else:
        if vjob.status.value == "completed":
            verification_result = "healthy"
        elif vjob.status.value == "failed":
            verification_result = "unhealthy"
            failure_type = VERIFICATION_FAILED
            failure_classification = VERIFICATION_FAILED

    ver_state, lifecycle_state = lifecycle_after_verification(
        verification_result=verification_result,
        failure_type=failure_classification or failure_type,
    )

    artifact = build_verification_artifact(
        provider=provider,
        operation=str(vjob.params.get("operation_type") or "verification"),
        target=str(target) if target else None,
        linked_mutation_execution=mutation_id,
        verification_result=verification_result,
        evidence={
            "readonly_execution": readonly_artifact,
            "provider_mutation_op": mutation_op,
            **extra,
        },
        readonly_job_id=verification_job_id,
    )

    if provider == "github" and mutation_op == "workflow_rerun":
        restart_verified = bool((extra.get("deployment_chain") or {}).get("chain_healthy"))
    else:
        restart_verified = bool(extra.get("verified")) if provider == "railway" else verification_result == "healthy"
    mjob.params["verification_state"] = ver_state
    mjob.params["verification_result"] = verification_result
    mjob.params["lifecycle_state"] = lifecycle_state
    mjob.params["verification_artifact"] = artifact
    mjob.params["verification_completed_at"] = time()
    mjob.params["verification_job_id"] = verification_job_id
    if provider == "github" and mutation_op == "workflow_rerun":
        mjob.params["verified"] = restart_verified
        if extra.get("rerun_outcome"):
            mjob.params["rerun_outcome"] = extra.get("rerun_outcome")
        if extra.get("deployment_chain"):
            mjob.params["deployment_chain"] = extra.get("deployment_chain")
        if extra.get("chain_summary"):
            mjob.params["chain_summary"] = extra.get("chain_summary")
        if extra.get("chain_verdict"):
            mjob.params["chain_verdict"] = extra.get("chain_verdict")
        if extra.get("proactive_verification_reply"):
            mjob.params["proactive_verification_reply"] = extra.get("proactive_verification_reply")
            mjob.params["latest_summary"] = extra.get("proactive_verification_reply")
    else:
        mjob.params["verified"] = restart_verified if provider == "railway" else verification_result == "healthy"
    if extra.get("restart_command_submitted") is not None:
        mjob.params["restart_command_submitted"] = extra["restart_command_submitted"]
    if extra.get("restart_verification_state"):
        mjob.params["restart_verification_state"] = extra["restart_verification_state"]
    if extra.get("transition_proof"):
        mjob.params["restart_transition_proof"] = extra["transition_proof"]
    if extra.get("provider_request"):
        mjob.params["restart_provider_request"] = extra["provider_request"]
    if extra.get("restart_transition"):
        mjob.params["restart_transition"] = extra["restart_transition"]
    if extra.get("service_health"):
        mjob.params["restart_service_health"] = extra["service_health"]
    if extra.get("final_verification"):
        mjob.params["restart_final_verification"] = extra["final_verification"]
    if isinstance(extra.get("before_snapshot"), dict):
        mjob.params["railway_before_snapshot"] = extra["before_snapshot"]
    if isinstance(extra.get("after_snapshot"), dict):
        mjob.params["railway_after_snapshot"] = extra["after_snapshot"]
    mjob.params["rollback_required"] = verification_result == "unhealthy"
    mjob.params["rollback_suggested"] = verification_result in ("unhealthy", "inconclusive")
    if retry_history:
        mjob.params["verification_retry_history"] = retry_history
    if failure_type:
        mjob.params["failure_type"] = failure_type
    if failure_classification:
        mjob.params["failure_classification"] = failure_classification

    rp = mjob.params.get("rollback_plan")
    if isinstance(rp, dict) and mjob.params.get("rollback_suggested"):
        rp = dict(rp)
        rp["rollback_suggested"] = True
        rp["recovery_guidance"] = [
            "Inspect readonly verification evidence",
            "Review deployment or workflow run state",
            "Consider redeploy prior deployment or repeat governed mutation with operator approval",
        ]
        mjob.params["rollback_plan"] = rp

    exec_artifact = mjob.params.get("mutation_execution")
    if isinstance(exec_artifact, dict):
        exec_artifact = dict(exec_artifact)
        exec_artifact["verification_result"] = verification_result
        exec_artifact["verification_artifact"] = artifact
        if failure_classification:
            exec_artifact["failure_classification"] = failure_classification
        pr = exec_artifact.get("provider_result")
        if isinstance(pr, dict) and provider == "github":
            pr = dict(pr)
            ev = dict(pr.get("evidence") or {})
            ev["verification_attempts"] = extra.get("verification_attempts", 0)
            ev["new_run_detected"] = extra.get("new_run_detected", False)
            if failure_classification:
                ev["failure_classification"] = failure_classification
            pr["evidence"] = ev
            exec_artifact["provider_result"] = pr
        mjob.params["mutation_execution"] = exec_artifact

    sync_mutation_job_lifecycle(mjob)
    from aethos_core.operation_lifecycle.operation_state_store import upsert_operation_state_from_job

    upsert_operation_state_from_job(mjob)
    return artifact
