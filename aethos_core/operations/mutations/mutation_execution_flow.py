# SPDX-License-Identifier: Apache-2.0
"""Approve mutation preflights and enqueue governed mutation_execution jobs."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from aethos_core.config import get_settings
from aethos_core.operations.mutations.approvals import can_approve_mutation
from aethos_core.operations.mutations.risk import MutationRiskTier, execution_allowed_for_tier
from aethos_core.operations.mutations.taxonomy import CANONICAL_MUTATION_EXECUTION_JOB_TYPE
from aethos_core.operations.orchestration.provider_runtime import stamp_execution_auth
from aethos_core.runtime.job_types import uses_mutation_preflight

MUTATION_APPROVABLE_STATUSES = frozenset(
    {
        "ready_for_mutation_approval",
    }
)


class MutationExecutionError(ValueError):
    pass


def validate_mutation_preflight_job(job: Any) -> dict[str, Any]:
    if not job:
        raise MutationExecutionError("Job not found")
    if not uses_mutation_preflight(job.job_type):
        raise MutationExecutionError("Not a mutation preflight job")
    if job.status.value != "completed":
        raise MutationExecutionError("Mutation preflight must complete before approval")
    if job.params.get("is_current") is False:
        raise MutationExecutionError("This mutation preflight was superseded — use the current one")

    pf = job.params.get("mutation_preflight") or {}
    status = str(job.params.get("preflight_status") or pf.get("preflight_status") or "")
    if status not in MUTATION_APPROVABLE_STATUSES:
        raise MutationExecutionError(f"Mutation preflight status not approvable: {status or 'unknown'}")
    provider = str(pf.get("provider") or job.params.get("provider") or "unknown")
    operation_type = str(pf.get("operation_type") or job.params.get("operation_type") or "")
    target_name = pf.get("target_name") or job.params.get("target_name")
    if provider == "railway":
        target_resolved = bool(job.params.get("target_resolved") or pf.get("target_resolved"))
        target_payload = job.params.get("target") or pf.get("target")
        if isinstance(target_payload, dict) and target_payload.get("resolved"):
            target_resolved = True
        if not target_resolved and not target_name:
            raise MutationExecutionError("Mutation target is unresolved — resolve target before approval")

    tier_value = str(job.params.get("risk_tier") or pf.get("risk_tier") or "")
    try:
        tier = MutationRiskTier(tier_value)
    except ValueError as exc:
        raise MutationExecutionError(f"Unknown risk tier: {tier_value}") from exc

    if tier == MutationRiskTier.T5_BLOCKED:
        raise MutationExecutionError("Blocked mutations cannot be approved")
    if tier == MutationRiskTier.T4_IRREVERSIBLE:
        raise MutationExecutionError("Irreversible mutations remain blocked")

    settings = get_settings()
    if not settings.mutation_execution_enabled:
        raise MutationExecutionError("Mutation execution is not enabled (set MUTATION_EXECUTION_ENABLED=true)")
    if tier == MutationRiskTier.T3_PRODUCTION and not settings.mutation_t3_production_enabled:
        raise MutationExecutionError(
            "Production-impacting mutations require MUTATION_T3_PRODUCTION_ENABLED=true"
        )
    if not execution_allowed_for_tier(tier):
        raise MutationExecutionError(f"Execution not enabled for tier {tier.value}")

    if job.params.get("mutation_execution_approved") or pf.get("mutation_execution_approved"):
        raise MutationExecutionError("Mutation already approved")

    exec_params: dict[str, Any] = {
        "provider": provider,
        "operation_type": operation_type,
        "target_name": target_name,
        "risk_tier": tier.value,
        "blast_radius": pf.get("blast_radius") or job.params.get("blast_radius"),
        "rollback_plan": pf.get("rollback_plan") or job.params.get("rollback_plan"),
        "audit": pf.get("audit") or job.params.get("audit"),
        "source_mutation_preflight_job_id": job.id,
        "preflight_job_id": job.id,
        "user_request": job.params.get("user_request") or pf.get("user_request"),
        "mutation_execution_approved": True,
        "mutating": True,
        "read_only": False,
        **stamp_execution_auth(provider=provider),
    }
    if job.params.get("env_var_reference"):
        exec_params["env_var_reference"] = job.params["env_var_reference"]
    if job.params.get("env_var_name"):
        exec_params["env_var_name"] = job.params["env_var_name"]
    if job.params.get("target_hints"):
        exec_params["target_hints"] = job.params["target_hints"]
    if job.params.get("target"):
        exec_params["target"] = job.params["target"]
    if job.params.get("target_resolved") is not None:
        exec_params["target_resolved"] = job.params["target_resolved"]
    if job.params.get("source_binding"):
        exec_params["source_binding"] = job.params["source_binding"]
    if job.params.get("source_binding_resolution"):
        exec_params["source_binding_resolution"] = job.params["source_binding_resolution"]

    from aethos_core.provider_topology.source_binding_resolver import (
        compose_stale_binding_regression_reply,
        refresh_params_source_binding,
    )

    refreshed, _resolution, regression = refresh_params_source_binding(
        exec_params,
        session_id=str(getattr(job, "session_id", None) or "default"),
        block_stale_regression=True,
    )
    if regression is not None:
        raise MutationExecutionError(compose_stale_binding_regression_reply(regression))
    exec_params.update(refreshed)
    wf = job.params.get("workflow_resolution") or (pf if isinstance(pf, dict) else {}).get("workflow_resolution")
    if isinstance(wf, dict) and wf.get("ok"):
        exec_params["workflow_resolution"] = wf
        from aethos_core.providers.github.shared.workflow_resolution import resolution_to_mutation_params

        exec_params.update(resolution_to_mutation_params(wf))
    return exec_params


def _capture_railway_snapshot_at_approval(exec_params: dict[str, Any]) -> None:
    provider = str(exec_params.get("provider") or "")
    operation = str(exec_params.get("operation_type") or "")
    if provider != "railway" or operation not in {"restart", "redeploy"}:
        return

    approved_iso = datetime.now(UTC).isoformat()
    exec_params["mutation_execution_approved_at_iso"] = approved_iso

    target = exec_params.get("target")
    service_id = None
    service_name = exec_params.get("target_name")
    if isinstance(target, dict):
        service_id = target.get("service_id")
        service_name = service_name or target.get("service_name")

    from aethos_core.providers.railway.mutations import resolve_railway_mutation_credentials

    token, _, _ = resolve_railway_mutation_credentials()
    if not token:
        return

    if not service_id and service_name:
        from aethos_core.providers.railway.api_client import find_service_by_name

        svc = find_service_by_name(token, str(service_name))
        if svc:
            service_id = svc.get("service_id")

    if not service_id:
        return

    from aethos_core.providers.railway.hardening.restart_transition import capture_railway_deployment_snapshot

    snapshot = capture_railway_deployment_snapshot(token, str(service_id), captured_at=approved_iso)
    exec_params["railway_before_snapshot"] = snapshot.to_dict()


def approve_mutation_execution(preflight_job_id: str) -> tuple[Any, Any]:
    """Returns (preflight_job, mutation_execution_job)."""
    from aethos_core.runtime.jobs import job_store

    preflight = job_store.get(preflight_job_id)
    exec_params = validate_mutation_preflight_job(preflight)
    _capture_railway_snapshot_at_approval(exec_params)
    provider = exec_params["provider"]
    operation_type = exec_params["operation_type"]
    target = exec_params.get("target_name")

    preflight.params["mutation_execution_approved"] = True
    preflight.params["mutation_execution_approved_at"] = __import__("time").time()

    title = f"Mutation execution — {operation_type.replace('_', ' ')}"
    if target:
        title += f" ({target})"

    execution = job_store.create(
        title=title,
        job_type=CANONICAL_MUTATION_EXECUTION_JOB_TYPE,
        params=exec_params,
        source="mutation_approval",
        session_id=preflight.session_id,
        auto_run=True,
    )
    execution.params["mutation_execution_job_id"] = execution.id
    exec_params["mutation_execution_job_id"] = execution.id

    pf = preflight.params.get("mutation_preflight") or {}
    if isinstance(pf, dict):
        pf["mutation_execution_approved"] = True
        pf["mutation_execution_job_id"] = execution.id
        preflight.params["mutation_preflight"] = pf

    preflight.params["mutation_execution_job_id"] = execution.id
    from aethos_core.operational_thread_memory.mutation_thread_memory import sync_thread_on_approval

    sync_thread_on_approval(preflight_job=preflight, execution_job=execution)
    from aethos_core.operation_lifecycle.operation_state_store import upsert_operation_state_from_job

    upsert_operation_state_from_job(preflight)
    upsert_operation_state_from_job(execution)
    try:  # §3 unified audit ledger — approval grant linked to the execution job.
        from aethos_core.observability.audit_ledger import record_audit_event

        record_audit_event(
            action="approval.grant",
            target=f"{provider}:{operation_type}:{target or '(none)'}",
            approval_id=preflight_job_id,
            ref=execution.id,
        )
    except Exception:  # noqa: BLE001
        pass
    return preflight, execution
