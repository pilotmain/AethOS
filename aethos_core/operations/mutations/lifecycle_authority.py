# SPDX-License-Identifier: Apache-2.0
"""Single source of truth for mutation lifecycle — summary, state, audit sync."""

from __future__ import annotations

from typing import Any

from aethos_core.operations.mutations.lifecycle import (
    EXECUTION_COMPLETED,
    EXECUTION_FAILED,
    EXECUTION_MUTATION_REQUESTED,
    EXECUTION_STABILIZING,
    LIFECYCLE_AWAITING_APPROVAL,
    LIFECYCLE_EXECUTION_COMPLETED,
    LIFECYCLE_EXECUTION_FAILED,
    LIFECYCLE_EXECUTING,
    LIFECYCLE_ROLLBACK_REQUIRED,
    LIFECYCLE_STABILIZING,
    LIFECYCLE_VERIFICATION_FAILED,
    LIFECYCLE_VERIFICATION_RUNNING,
    LIFECYCLE_VERIFIED,
    VERIFICATION_FAILED,
    VERIFICATION_PENDING,
    VERIFICATION_RUNNING,
    VERIFICATION_VERIFIED,
)

# Canonical mutation runtime state machine (Phase 9.6.3)
PREFLIGHT_PENDING = "preflight_pending"
AWAITING_APPROVAL = "awaiting_approval"
APPROVED = "approved"
EXECUTION_RUNNING = "execution_running"
EXECUTION_COMPLETED_STATE = "execution_completed"
EXECUTION_FAILED_STATE = "execution_failed"
VERIFICATION_RUNNING_STATE = "verification_running"
VERIFIED_STATE = "verified"
VERIFICATION_FAILED_STATE = "verification_failed"
VERIFICATION_TIMEOUT_STATE = "verification_timeout"
VERIFICATION_INCONCLUSIVE_STATE = "verification_inconclusive"
ROLLBACK_REQUIRED_STATE = "rollback_required"
PROVIDER_MUTATION_REQUESTED_STATE = "provider_mutation_requested"
STABILIZING_STATE = "stabilizing"
DISCOVERY_FAILED_STATE = "discovery_failed"
NEEDS_WORKFLOW_RESOLUTION = "needs_workflow_resolution"
AUDIT_RECORDED = "audit_recorded"


def canonical_mutation_state(params: dict[str, Any]) -> str:
    """Derive authoritative lifecycle state from mutation job params."""
    if params.get("rollback_required") or params.get("lifecycle_state") == LIFECYCLE_ROLLBACK_REQUIRED:
        return ROLLBACK_REQUIRED_STATE
    failure = str(params.get("failure_type") or "")
    if failure == "verification_timeout":
        return VERIFICATION_TIMEOUT_STATE
    ver = str(params.get("verification_state") or "")
    if ver == VERIFICATION_VERIFIED or params.get("verified") is True:
        if params.get("audit"):
            return AUDIT_RECORDED
        return VERIFIED_STATE
    if ver == VERIFICATION_FAILED:
        return VERIFICATION_FAILED_STATE
    if ver == VERIFICATION_RUNNING:
        return VERIFICATION_RUNNING_STATE
    if params.get("verification_result") == "inconclusive":
        return VERIFICATION_INCONCLUSIVE_STATE
    exec_state = str(params.get("execution_state") or "")
    if exec_state in {EXECUTION_MUTATION_REQUESTED, EXECUTION_STABILIZING}:
        if params.get("verification_job_id") or str(params.get("verification_state") or "") in {
            VERIFICATION_PENDING,
            VERIFICATION_RUNNING,
        }:
            return STABILIZING_STATE
        return PROVIDER_MUTATION_REQUESTED_STATE
    if exec_state == EXECUTION_FAILED or (params.get("executed") is False and not params.get("dry_run")):
        return EXECUTION_FAILED_STATE
    if params.get("verification_job_id") and ver == VERIFICATION_PENDING:
        return VERIFICATION_RUNNING_STATE if params.get("lifecycle_state") == LIFECYCLE_VERIFICATION_RUNNING else VERIFICATION_RUNNING_STATE
    if exec_state == EXECUTION_COMPLETED or params.get("executed") is True:
        if params.get("verification_job_id"):
            return VERIFICATION_RUNNING_STATE
        return EXECUTION_COMPLETED_STATE
    if params.get("mutation_execution_approved"):
        return APPROVED
    preflight = str(params.get("preflight_status") or "")
    if preflight in ("needs_workflow_resolution", "needs_information") and params.get("discovery_failure_reason"):
        return DISCOVERY_FAILED_STATE
    if preflight == "needs_workflow_resolution":
        return NEEDS_WORKFLOW_RESOLUTION
    if preflight == "ready_for_mutation_approval":
        return AWAITING_APPROVAL
    return PREFLIGHT_PENDING


def mutation_summary(
    *,
    provider: str,
    operation_type: str,
    target: str,
    canonical_state: str,
    failure_classification: str | None = None,
) -> str:
    op = operation_type.replace("_", " ")
    base = f"Mutation {op} on {target}"
    request_phrase = f"{op} requested" if operation_type in {"restart", "redeploy"} else f"{op} submitted"
    summaries: dict[str, str] = {
        PROVIDER_MUTATION_REQUESTED_STATE: f"{base} · {request_phrase} · verification pending",
        STABILIZING_STATE: f"{base} · {request_phrase} · stabilizing",
        EXECUTION_COMPLETED_STATE: f"{base} · execution completed · verification pending",
        EXECUTION_FAILED_STATE: f"{base} · execution failed",
        VERIFICATION_RUNNING_STATE: f"{base} · execution completed · verification running",
        VERIFIED_STATE: f"{base} · execution completed · verified healthy",
        AUDIT_RECORDED: f"{base} · execution completed · verified healthy · audit recorded",
        VERIFICATION_FAILED_STATE: f"{base} · execution completed · verification failed",
        VERIFICATION_TIMEOUT_STATE: f"{base} · execution completed · verification timeout",
        VERIFICATION_INCONCLUSIVE_STATE: f"{base} · execution completed · verification inconclusive",
        ROLLBACK_REQUIRED_STATE: f"{base} · rollback suggested",
        DISCOVERY_FAILED_STATE: f"{base} · discovery failed",
        NEEDS_WORKFLOW_RESOLUTION: f"{base} · needs workflow resolution",
    }
    text = summaries.get(canonical_state, f"{base} · {canonical_state.replace('_', ' ')}")
    if failure_classification and canonical_state in (
        EXECUTION_FAILED_STATE,
        VERIFICATION_FAILED_STATE,
        VERIFICATION_TIMEOUT_STATE,
        ROLLBACK_REQUIRED_STATE,
    ):
        text = f"{text} · {failure_classification.replace('_', ' ')}"
    return text


def sync_mutation_job_lifecycle(job: Any) -> dict[str, str]:
    """Recompute canonical state + summary and propagate to artifact/audit."""
    params = job.params
    provider = str(params.get("provider") or "unknown")
    operation = str(params.get("operation_type") or "unknown")
    target = str(params.get("target_name") or "(none)")
    failure = params.get("failure_type") or params.get("failure_classification")
    failure_str = str(failure) if failure else None

    state = canonical_mutation_state(params)
    summary = mutation_summary(
        provider=provider,
        operation_type=operation,
        target=target,
        canonical_state=state,
        failure_classification=failure_str,
    )

    params["canonical_lifecycle_state"] = state
    params["lifecycle_summary"] = summary

    exec_artifact = params.get("mutation_execution")
    if isinstance(exec_artifact, dict):
        exec_artifact = dict(exec_artifact)
        exec_artifact["canonical_lifecycle_state"] = state
        exec_artifact["lifecycle_summary"] = summary
        exec_artifact["verification_state"] = params.get("verification_state")
        exec_artifact["lifecycle_state"] = params.get("lifecycle_state")
        if failure_str:
            exec_artifact["failure_classification"] = failure_str
        params["mutation_execution"] = exec_artifact

    audit = params.get("audit")
    if isinstance(audit, dict):
        audit = dict(audit)
        audit["canonical_lifecycle_state"] = state
        audit["lifecycle_summary"] = summary
        audit["verification_state"] = params.get("verification_state")
        if failure_str:
            audit["failure_classification"] = failure_str
        params["audit"] = audit

    job.result_summary = summary
    return {"canonical_lifecycle_state": state, "lifecycle_summary": summary}
