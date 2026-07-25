# SPDX-License-Identifier: Apache-2.0
"""Approve completed preflights and enqueue read-only execution jobs."""

from __future__ import annotations

from typing import Any

from aethos_core.operations.execution.execution_permissions import (
    actions_for_operation,
    is_mutating_operation,
)
from aethos_core.operations.orchestration.job_taxonomy import canonical_readonly_execution_job_type
from aethos_core.operations.orchestration.registry_runtime import (
    preflight_capability_metadata,
    resolve_provider_execution_auth,
)
from aethos_core.runtime.job_types import uses_operation_preflight

APPROVABLE_STATUSES = frozenset(
    {
        "ready_for_approval",
        "ready_for_readonly_diagnostic",
    }
)


class PreflightExecutionError(ValueError):
    pass


def validate_preflight_job(job: Any) -> dict[str, Any]:
    if not job:
        raise PreflightExecutionError("Job not found")
    if not uses_operation_preflight(job.job_type):
        raise PreflightExecutionError("Not an operation preflight job")
    if job.status.value != "completed":
        raise PreflightExecutionError("Preflight must complete before approval")
    if job.params.get("is_current") is False:
        raise PreflightExecutionError("This preflight was superseded — use the current one")
    pf = job.params.get("operation_preflight") or {}
    status = str(job.params.get("preflight_status") or pf.get("preflight_status") or "")
    if status == "superseded":
        raise PreflightExecutionError("Superseded preflight cannot be approved")
    if status == "needs_information":
        raise PreflightExecutionError("Preflight still needs information before execution")
    if status not in APPROVABLE_STATUSES:
        raise PreflightExecutionError(f"Preflight status not approvable: {status or 'unknown'}")
    provider = str(pf.get("provider") or job.params.get("provider") or "unknown")
    operation_type = str(pf.get("operation_type") or job.params.get("operation_type") or "")
    if is_mutating_operation(operation_type):
        raise PreflightExecutionError("Mutating operations are not enabled in Phase 9.3")
    missing = list(pf.get("missing_information") or [])
    if missing and operation_type == "set_env_var":
        raise PreflightExecutionError("Resolve missing env information before execution")
    if pf.get("target_status") == "missing" and provider in ("vercel", "railway", "github"):
        raise PreflightExecutionError("Resolve target project before execution")
    current_state = pf.get("current_state") if isinstance(pf.get("current_state"), dict) else {}
    production_url = current_state.get("production_url") or pf.get("production_url")
    return {
        "provider": provider,
        "operation_type": operation_type,
        "target_name": pf.get("target_name"),
        "production_url": production_url,
        "approved_actions": actions_for_operation(operation_type, provider=provider),
        "operation_preflight": pf,
        "source_preflight_job_id": job.id,
        "profile_id": job.params.get("profile_id"),
        "user_request": job.params.get("user_request") or pf.get("user_request"),
        **_execution_auth(provider),
        **preflight_capability_metadata(provider, operation_type),
    }


def _execution_auth(provider: str) -> dict[str, Any]:
    return resolve_provider_execution_auth(provider)


def execution_job_type_for(provider: str) -> str:
    return canonical_readonly_execution_job_type(provider)


def approve_preflight_readonly_execution(preflight_job_id: str) -> tuple[Any, Any]:
    """Returns (preflight_job, execution_job)."""
    from aethos_core.runtime.jobs import job_store

    preflight = job_store.get(preflight_job_id)
    exec_params = validate_preflight_job(preflight)
    provider = exec_params["provider"]
    operation_type = exec_params["operation_type"]
    target = exec_params.get("target_name")

    preflight.params["execution_approved"] = True
    preflight.params["execution_approved_at"] = __import__("time").time()

    title = f"Read-only execution — {operation_type.replace('_', ' ')}"
    if target:
        title += f" ({target})"

    execution = job_store.create(
        title=title,
        job_type=execution_job_type_for(provider),
        params={
            **exec_params,
            "read_only": True,
            "mutating": False,
        },
        source="preflight_approval",
        session_id=preflight.session_id,
        auto_run=True,
    )

    pf = preflight.params.get("operation_preflight") or {}
    if isinstance(pf, dict):
        pf["execution_approved"] = True
        pf["execution_job_id"] = execution.id
        pf["read_only_execution_enabled"] = True
        preflight.params["operation_preflight"] = pf
        from aethos_core.operations.operation_models import OperationPreflight
        from aethos_core.operations.preflight import refresh_preflight_report

        pf_obj = OperationPreflight.from_dict(pf)
        report = refresh_preflight_report(
            pf_obj,
            user_request=str(preflight.params.get("user_request") or pf.get("user_request") or ""),
        )
        preflight.full_result = report
        preflight.result = report

    preflight.params["execution_job_id"] = execution.id
    return preflight, execution
