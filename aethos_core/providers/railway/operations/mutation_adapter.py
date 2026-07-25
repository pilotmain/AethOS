# SPDX-License-Identifier: Apache-2.0
"""Railway mutation adapter — governed restart/redeploy."""

from __future__ import annotations

from typing import Any

from aethos_core.config import get_settings
from aethos_core.providers.base.mutation_adapter import MutationAdapter, MutationNotEnabledError
from aethos_core.providers.railway.mutations import execute_railway_mutation, resolve_railway_mutation_credentials
from aethos_core.providers.railway.mutations import _provider_target_from_params
from aethos_core.providers.railway.restart_diagnostics import diagnose_railway_mutation_target


class RailwayMutationAdapter(MutationAdapter):
    provider = "railway"

    @property
    def enabled(self) -> bool:
        return get_settings().mutation_execution_enabled

    def supported_mutations(self) -> list[str]:
        ops = ["restart", "redeploy", "stop"]
        if get_settings().provider_env_var_mutations_enabled:
            ops.append("set_env_var")
        return ops

    def dry_run(self, *, operation: str, params: dict[str, Any]) -> dict[str, Any]:
        target = _provider_target_from_params(params)
        token, source, cred_error = resolve_railway_mutation_credentials()
        if not token:
            return {
                "ok": False,
                "dry_run": True,
                "operation": operation,
                "target_name": target.service_name,
                "detail": cred_error or "Railway mutation credentials are not configured.",
                "credential_source": source,
            }
        diagnostics = diagnose_railway_mutation_target(
            token,
            target=target,
            operation=operation,
            credential_source=source,
        )
        diag = diagnostics.to_dict()
        lines = [
            f"Would execute governed `{operation}` on Railway service `{target.service_name}`.",
            f"Provider operation: `{diag.get('planned_graphql_operation')}`",
            f"Service ID: `{diag.get('service_id')}`",
            f"Project: `{diag.get('project_name')}` (`{diag.get('project_id')}`)",
            f"Environment: `{diag.get('environment_name')}` (`{diag.get('environment_id')}`)",
            f"Deployment ID: `{diag.get('deployment_id')}`",
            f"Mutation variables: `{diag.get('planned_mutation_variables')}`",
            f"Write access: `{diag.get('write_access')}`",
        ]
        if diagnostics.issues:
            lines.append("Issues: " + "; ".join(diagnostics.issues))
        return {
            "ok": diagnostics.ok,
            "dry_run": True,
            "operation": operation,
            "target_name": target.service_name,
            "detail": "\n".join(lines),
            "mutation_diagnostics": diag,
            "credential_source": source,
        }

    def execute(self, *, operation: str, params: dict[str, Any]) -> dict[str, Any]:
        self.assert_enabled()
        if operation not in self.supported_mutations():
            raise MutationNotEnabledError(f"Unsupported Railway mutation: {operation}")
        request_id = str(params.get("mutation_execution_job_id") or params.get("source_mutation_preflight_job_id") or "railway-mutation")
        return execute_railway_mutation(operation=operation, params=params, request_id=request_id)
