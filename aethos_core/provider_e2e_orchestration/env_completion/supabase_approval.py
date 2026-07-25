# SPDX-License-Identifier: Apache-2.0
"""Supabase env completion — approval gate and flow."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Literal

from aethos_core.config import get_settings
from aethos_core.provider_e2e_orchestration.env_completion.supabase_constants import (
    SUPABASE_ENV_COMPLETION_JOB_TYPE,
)

FailureState = Literal[
    "missing_approval",
    "mutation_execution_disabled",
    "production_gate_required",
    "env_var_mutations_disabled",
    "missing_provider_token",
    "missing_target_project",
    "not_completion_job",
    "already_approved",
    "invalid_job",
    "browser_automation_disabled",
]


@dataclass
class SupabaseEnvCompletionApprovalResult:
    ok: bool
    failure_state: FailureState | None = None
    detail: str = ""
    report: dict[str, Any] | None = None


class SupabaseEnvCompletionApprovalError(ValueError):
    pass


def validate_supabase_env_completion_gate(job: Any, *, for_execution: bool = False) -> SupabaseEnvCompletionApprovalResult:
    if not job:
        return SupabaseEnvCompletionApprovalResult(ok=False, failure_state="invalid_job", detail="Job not found")

    if str(getattr(job, "job_type", "") or "") != SUPABASE_ENV_COMPLETION_JOB_TYPE:
        return SupabaseEnvCompletionApprovalResult(
            ok=False,
            failure_state="not_completion_job",
            detail="Not a Supabase env completion job.",
        )

    params = dict(getattr(job, "params", None) or {})
    settings = get_settings()
    project_name = str(params.get("project_name") or (params.get("target") or {}).get("project_name") or "")
    checks: dict[str, Any] = {
        "project_name": project_name,
        "referenced_github_repo": str(params.get("referenced_github_repo") or ""),
        "missing_env_names": list(params.get("missing_env_names") or []),
        "mutation_execution_enabled": settings.mutation_execution_enabled,
        "provider_env_var_mutations_enabled": settings.provider_env_var_mutations_enabled,
        "browser_automation_enabled": settings.browser_automation_enabled,
    }

    if for_execution and not params.get("supabase_env_completion_approved"):
        return SupabaseEnvCompletionApprovalResult(
            ok=False,
            failure_state="missing_approval",
            detail="Supabase env completion requires explicit Mission Control approval.",
            report=checks,
        )

    if params.get("supabase_env_completion_approved") and not for_execution:
        return SupabaseEnvCompletionApprovalResult(
            ok=False,
            failure_state="already_approved",
            detail="Supabase env completion already approved.",
        )

    if not settings.mutation_execution_enabled:
        return SupabaseEnvCompletionApprovalResult(
            ok=False,
            failure_state="mutation_execution_disabled",
            detail="Set MUTATION_EXECUTION_ENABLED=true for governed execution.",
            report=checks,
        )

    if not settings.provider_env_var_mutations_enabled:
        return SupabaseEnvCompletionApprovalResult(
            ok=False,
            failure_state="env_var_mutations_disabled",
            detail="Set PROVIDER_ENV_VAR_MUTATIONS_ENABLED=true to write Vercel env vars.",
            report=checks,
        )

    if not project_name:
        return SupabaseEnvCompletionApprovalResult(
            ok=False,
            failure_state="missing_target_project",
            detail="Target Vercel project name is required.",
            report=checks,
        )

    if not str(params.get("credential_id") or "").strip():
        from aethos_core.providers.vercel.auth import VercelAuthAdapter

        auth = VercelAuthAdapter().resolve_best_auth_method(operation="read_projects")
        if auth.get("method") != "api_token" or not auth.get("credential_id"):
            return SupabaseEnvCompletionApprovalResult(
                ok=False,
                failure_state="missing_provider_token",
                detail="Validated Vercel API token required in Mission Control → Advanced settings → Credentials.",
                report=checks,
            )
        params["credential_id"] = str(auth.get("credential_id") or "")

    return SupabaseEnvCompletionApprovalResult(ok=True, report=checks)


def approve_supabase_env_completion(job_id: str) -> tuple[Any, dict[str, Any]]:
    from aethos_core.runtime.job_executor import job_executor
    from aethos_core.runtime.jobs import job_store

    job = job_store.get(job_id)
    gate = validate_supabase_env_completion_gate(job, for_execution=False)
    if not gate.ok:
        raise SupabaseEnvCompletionApprovalError(gate.detail or gate.failure_state or "approval blocked")

    approval_id = f"supabase-env-{job_id}-{int(datetime.now(UTC).timestamp())}"
    job.params["supabase_env_completion_approved"] = True
    job.params["approval_id"] = approval_id
    job.params["execution_status"] = "approved"
    job.params["approval_gate_report"] = gate.report or {}
    job.params["supabase_env_completion_approved_at_iso"] = datetime.now(UTC).isoformat()
    job_executor.enqueue(job_id)
    return job, {"approval_id": approval_id, "gate": job.params["approval_gate_report"]}
