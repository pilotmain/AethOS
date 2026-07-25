# SPDX-License-Identifier: Apache-2.0
"""Railway restart diagnostics — resolve IDs and plan provider mutations without mutating."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from aethos_core.config import get_settings
from aethos_core.providers.railway.target_resolver import ProviderTarget


@dataclass
class RailwayMutationDiagnostics:
    ok: bool
    service_id: str | None = None
    service_name: str | None = None
    project_id: str | None = None
    project_name: str | None = None
    environment_id: str | None = None
    environment_name: str | None = None
    deployment_id: str | None = None
    deployment_status: str | None = None
    deployment_created_at: str | None = None
    planned_graphql_operation: str | None = None
    planned_mutation_variables: dict[str, Any] = field(default_factory=dict)
    governed_operation: str = "restart"
    recommended_provider_operation: str = "serviceInstanceRedeploy"
    credential_source: str = "unknown"
    write_access: str = "unknown"
    issues: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "service_id": self.service_id,
            "service_name": self.service_name,
            "project_id": self.project_id,
            "project_name": self.project_name,
            "environment_id": self.environment_id,
            "environment_name": self.environment_name,
            "deployment_id": self.deployment_id,
            "deployment_status": self.deployment_status,
            "deployment_created_at": self.deployment_created_at,
            "planned_graphql_operation": self.planned_graphql_operation,
            "planned_mutation_variables": dict(self.planned_mutation_variables),
            "governed_operation": self.governed_operation,
            "recommended_provider_operation": self.recommended_provider_operation,
            "credential_source": self.credential_source,
            "write_access": self.write_access,
            "issues": list(self.issues),
        }


def _preferred_environment_name(target: ProviderTarget) -> str:
    return str(target.environment or "production").strip().lower() or "production"


def diagnose_railway_mutation_target(
    token: str,
    *,
    target: ProviderTarget,
    operation: str = "restart",
    credential_source: str = "unknown",
) -> RailwayMutationDiagnostics:
    """Resolve Railway IDs and plan the provider mutation without executing it."""
    from aethos_core.providers.railway.api_client import find_service_by_name, list_service_deployments
    from aethos_core.providers.railway.operations.mutations_api import resolve_environment_id

    settings = get_settings()
    issues: list[str] = []
    service_name = str(target.service_name or "").strip()
    service_id = str(target.service_id or "").strip() or None
    project_id = str(settings.railway_project_id or "").strip() or None
    project_name = target.project_name
    environment_id = str(settings.railway_environment_id or "").strip() or None
    environment_name = _preferred_environment_name(target)

    if not service_name and not service_id:
        return RailwayMutationDiagnostics(
            ok=False,
            governed_operation=operation,
            credential_source=credential_source,
            issues=["Target service name or service_id required."],
        )

    svc = None
    if service_id:
        from aethos_core.providers.railway.api_client import list_services

        for row in list_services(token):
            if str(row.get("service_id") or "") == service_id:
                svc = row
                break
    if svc is None and service_name:
        svc = find_service_by_name(token, service_name)

    if not svc:
        return RailwayMutationDiagnostics(
            ok=False,
            service_name=service_name or None,
            service_id=service_id,
            governed_operation=operation,
            credential_source=credential_source,
            issues=[f"Railway service `{service_name or service_id}` not found."],
        )

    service_id = str(svc.get("service_id") or service_id or "")
    service_name = str(svc.get("service_name") or service_name)
    project_id = project_id or str(svc.get("project_id") or "") or None
    project_name = project_name or svc.get("project_name")

    if project_id and not environment_id:
        resolved_env = resolve_environment_id(
            token,
            project_id=project_id,
            preferred_name=environment_name,
        )
        if resolved_env:
            environment_id = resolved_env.get("environment_id")
            environment_name = resolved_env.get("environment_name") or environment_name
        else:
            issues.append("Could not resolve Railway environment id for project.")

    deployments = list_service_deployments(token, service_id=service_id, limit=5) if service_id else []
    latest = deployments[0] if deployments else {}
    deployment_id = str(latest.get("id") or "") or None
    deployment_status = str(latest.get("state") or "") or None
    deployment_created_at = latest.get("created_at")

    if not deployments:
        issues.append("No deployments found for service.")
    if not deployment_id:
        issues.append("Latest deployment id unavailable.")

    provider_operation = (settings.railway_restart_provider_operation or "service_instance_redeploy").strip().lower()
    if operation == "redeploy":
        provider_operation = "service_instance_redeploy"
    if operation == "stop":
        planned_graphql = "deploymentStop"
        planned_vars = {"id": deployment_id} if deployment_id else {}
        if not deployment_id:
            issues.append("deployment_id missing — deploymentStop requires latest deployment id.")
        recommended = "deploymentStop"
    elif provider_operation in {"service_instance_redeploy", "serviceinstanceredeploy"}:
        planned_graphql = "serviceInstanceRedeploy"
        planned_vars: dict[str, Any] = {}
        if environment_id and service_id:
            planned_vars = {"environmentId": environment_id, "serviceId": service_id}
        else:
            if not environment_id:
                issues.append("environment_id missing — serviceInstanceRedeploy requires environmentId + serviceId.")
            if not service_id:
                issues.append("service_id missing — serviceInstanceRedeploy requires environmentId + serviceId.")
        recommended = "serviceInstanceRedeploy"
    else:
        planned_graphql = "deploymentRestart"
        planned_vars = {"id": deployment_id} if deployment_id else {}
        if not deployment_id:
            issues.append("deployment_id missing — deploymentRestart requires latest deployment id.")
        recommended = "deploymentRestart"

    write_access = "unknown"
    if project_id and environment_id:
        write_access = "mutation_scope_resolved"
    elif project_id:
        write_access = "readonly_ok"

    if target.project_name and project_name and str(target.project_name).lower() not in str(project_name).lower():
        issues.append(
            f"Resolved project `{project_name}` may not match requested project `{target.project_name}`."
        )

    ok = not issues and bool(planned_vars)
    return RailwayMutationDiagnostics(
        ok=ok,
        service_id=service_id or None,
        service_name=service_name or None,
        project_id=project_id,
        project_name=str(project_name) if project_name else None,
        environment_id=environment_id,
        environment_name=environment_name,
        deployment_id=deployment_id,
        deployment_status=deployment_status,
        deployment_created_at=str(deployment_created_at) if deployment_created_at else None,
        planned_graphql_operation=planned_graphql,
        planned_mutation_variables=planned_vars,
        governed_operation=operation,
        recommended_provider_operation=recommended,
        credential_source=credential_source,
        write_access=write_access,
        issues=issues,
    )


def diagnose_railway_restart_target(
    token: str,
    *,
    target: ProviderTarget,
    credential_source: str = "unknown",
) -> RailwayMutationDiagnostics:
    return diagnose_railway_mutation_target(
        token,
        target=target,
        operation="restart",
        credential_source=credential_source,
    )
