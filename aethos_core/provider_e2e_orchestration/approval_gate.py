# SPDX-License-Identifier: Apache-2.0
"""Approval gate validation for provider E2E orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from aethos_core.config import get_settings
from aethos_core.provider_e2e_execution.job_taxonomy import PROVIDER_E2E_ORCHESTRATION_JOB_TYPE
from aethos_core.provider_e2e_orchestration.job_model import build_provider_e2e_job_model

FailureState = Literal[
    "missing_approval",
    "mutation_execution_disabled",
    "production_gate_required",
    "env_var_mutations_disabled",
    "missing_provider_token",
    "missing_target_service",
    "not_orchestration_job",
    "already_approved",
    "invalid_job",
]


@dataclass
class ApprovalGateResult:
    ok: bool
    failure_state: FailureState | None = None
    detail: str = ""
    report: dict[str, Any] | None = None


class ProviderE2EApprovalError(ValueError):
    pass


def _is_production_target(model) -> bool:
    env = (model.environment or "").lower()
    return env in {"production", "prod"} or "production" in env


def validate_approval_gate(job: Any, *, for_execution: bool = False) -> ApprovalGateResult:
    """Validate Mission Control approval prerequisites."""
    if not job:
        return ApprovalGateResult(ok=False, failure_state="invalid_job", detail="Job not found")

    if str(getattr(job, "job_type", "") or "") != PROVIDER_E2E_ORCHESTRATION_JOB_TYPE:
        return ApprovalGateResult(ok=False, failure_state="not_orchestration_job", detail="Not a provider E2E job")

    params = dict(getattr(job, "params", None) or {})
    model = build_provider_e2e_job_model(params)
    settings = get_settings()

    checks: dict[str, Any] = {
        "provider": model.provider,
        "environment": model.environment,
        "service_name": model.service_name,
        "project_name": model.project_name,
        "mutation_execution_enabled": settings.mutation_execution_enabled,
        "provider_env_var_mutations_enabled": settings.provider_env_var_mutations_enabled,
        "t3_production_enabled": settings.mutation_t3_production_enabled,
    }

    if for_execution and not params.get("provider_e2e_approved"):
        return ApprovalGateResult(
            ok=False,
            failure_state="missing_approval",
            detail="Provider E2E orchestration requires explicit Mission Control approval.",
            report=checks,
        )

    if params.get("provider_e2e_approved") and not for_execution:
        return ApprovalGateResult(ok=False, failure_state="already_approved", detail="Orchestration already approved.")

    if not settings.mutation_execution_enabled:
        return ApprovalGateResult(
            ok=False,
            failure_state="mutation_execution_disabled",
            detail="Set MUTATION_EXECUTION_ENABLED=true for governed execution.",
            report=checks,
        )

    if model.env_var_names and not settings.provider_env_var_mutations_enabled:
        return ApprovalGateResult(
            ok=False,
            failure_state="env_var_mutations_disabled",
            detail="Env var application requires PROVIDER_ENV_VAR_MUTATIONS_ENABLED=true.",
            report=checks,
        )

    if _is_production_target(model) and not settings.mutation_t3_production_enabled:
        return ApprovalGateResult(
            ok=False,
            failure_state="production_gate_required",
            detail="Production targets require MUTATION_T3_PRODUCTION_ENABLED=true.",
            report=checks,
        )

    if model.provider == "railway":
        from aethos_core.providers.railway.mutations import resolve_railway_mutation_credentials

        is_greenfield = bool(params.get("greenfield")) and str(params.get("flow") or "") == "railway_greenfield_deployment"
        token, _, err = resolve_railway_mutation_credentials()
        if not token:
            return ApprovalGateResult(
                ok=False,
                failure_state="missing_provider_token",
                detail=err or "Railway token not configured.",
                report=checks,
            )
        if not is_greenfield and not model.service_name:
            return ApprovalGateResult(
                ok=False,
                failure_state="missing_target_service",
                detail="Railway service target is required.",
                report=checks,
            )

    if model.provider == "vercel":
        from aethos_core.providers.vercel.auth import VercelAuthAdapter

        auth = VercelAuthAdapter()
        resolved = auth.resolve_best_auth_method(operation="read_projects")
        if resolved.get("method") != "api_token":
            return ApprovalGateResult(
                ok=False,
                failure_state="missing_provider_token",
                detail=str(resolved.get("detail") or "Vercel token not configured."),
                report=checks,
            )
        if not model.project_name:
            return ApprovalGateResult(
                ok=False,
                failure_state="missing_target_service",
                detail="Vercel project name is required.",
                report=checks,
            )

    return ApprovalGateResult(ok=True, report=checks)


def build_approval_gate_validation_report(result: ApprovalGateResult) -> dict[str, Any]:
    return {
        "ok": result.ok,
        "failure_state": result.failure_state,
        "detail": result.detail,
        "checks": result.report or {},
    }
