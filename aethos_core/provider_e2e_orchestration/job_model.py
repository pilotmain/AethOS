# SPDX-License-Identifier: Apache-2.0
"""Provider E2E orchestration job model — names only in evidence, never secret values."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

_EXECUTION_STATUSES = frozenset(
    {
        "awaiting_approval",
        "approved",
        "running",
        "env_failed",
        "redeploy_failed",
        "polling_failed",
        "verification_failed",
        "completed",
        "failed",
        "blocked",
    }
)

DeployAction = Literal["redeploy", "none"]
ExecutionStatus = Literal[
    "awaiting_approval",
    "approved",
    "running",
    "env_failed",
    "redeploy_failed",
    "polling_failed",
    "verification_failed",
    "completed",
    "failed",
    "blocked",
]


@dataclass
class ProviderE2EJobModel:
    provider: str
    project_id: str = ""
    project_name: str = ""
    service_id: str = ""
    service_name: str = ""
    environment: str = "production"
    env_var_names: list[str] = field(default_factory=list)
    env_var_values_source: str = "secure_store"
    deploy_action: DeployAction = "redeploy"
    health_check_url: str = ""
    approval_id: str = ""
    execution_status: ExecutionStatus = "awaiting_approval"
    credential_id: str = ""
    evidence: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "project_id": self.project_id,
            "project_name": self.project_name,
            "service_id": self.service_id,
            "service_name": self.service_name,
            "environment": self.environment,
            "env_var_names": list(self.env_var_names),
            "env_var_values_source": self.env_var_values_source,
            "deploy_action": self.deploy_action,
            "health_check_url": self.health_check_url,
            "approval_id": self.approval_id,
            "execution_status": self.execution_status,
            "credential_id": self.credential_id,
            "evidence": dict(self.evidence),
        }


def _target_from_params(params: dict[str, Any]) -> dict[str, Any]:
    target = params.get("target")
    return dict(target) if isinstance(target, dict) else {}


def build_provider_e2e_job_model(params: dict[str, Any]) -> ProviderE2EJobModel:
    """Normalize orchestration job params into the sprint-002 schema."""
    target = _target_from_params(params)
    provider = str(params.get("provider") or "")
    env_names = params.get("env_var_names")
    if not isinstance(env_names, list):
        env_names = []
    env_names = [str(n).strip().upper() for n in env_names if str(n).strip()]

    status_raw = str(params.get("execution_status") or "awaiting_approval")
    status: ExecutionStatus = status_raw if status_raw in _EXECUTION_STATUSES else "awaiting_approval"  # type: ignore[assignment]

    deploy = str(params.get("deploy_action") or "redeploy")
    if deploy not in {"redeploy", "none"}:
        deploy = "redeploy"

    return ProviderE2EJobModel(
        provider=provider,
        project_id=str(params.get("project_id") or target.get("project_id") or ""),
        project_name=str(params.get("project_name") or target.get("project_name") or ""),
        service_id=str(params.get("service_id") or target.get("service_id") or ""),
        service_name=str(params.get("service_name") or target.get("service_name") or params.get("target_name") or ""),
        environment=str(params.get("environment") or target.get("environment_name") or target.get("environment") or "production"),
        env_var_names=env_names,
        env_var_values_source=str(params.get("env_var_values_source") or "secure_store"),
        deploy_action=deploy,  # type: ignore[arg-type]
        health_check_url=str(params.get("health_check_url") or ""),
        approval_id=str(params.get("approval_id") or ""),
        execution_status=status,
        credential_id=str(params.get("credential_id") or ""),
        evidence=dict(params.get("evidence") or {}),
    )


def enrich_job_params_for_orchestration(params: dict[str, Any]) -> dict[str, Any]:
    """Attach normalized model fields when creating an orchestration preflight job."""
    model = build_provider_e2e_job_model(params)
    out = dict(params)
    out.update(model.to_dict())
    out.setdefault("execution_status", "awaiting_approval")
    out.setdefault("deploy_action", "redeploy")
    out.setdefault("env_var_values_source", "secure_store")
    out.setdefault("provider_e2e_approved", False)
    out.setdefault("evidence", {})
    if not out.get("env_var_names"):
        if model.provider == "railway":
            from aethos_core.providers.railway.env_value_readiness.env_minimum_secret_sets import (
                minimum_secrets_for_profile,
            )

            profile = "railway_production" if "prod" in model.environment.lower() else "railway_staging"
            out["env_var_names"] = list(minimum_secrets_for_profile(profile))
        elif model.provider == "vercel":
            out["env_var_names"] = []
    return out
