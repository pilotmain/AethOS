# SPDX-License-Identifier: Apache-2.0
"""Railway provider discovery — dynamic workspace topology."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from aethos_core.config import get_settings
from aethos_core.provider_discovery.provider_capabilities import service_supported_operations
from aethos_core.provider_discovery.provider_inventory import (
    ProviderDeploymentRecord,
    ProviderEnvironmentRecord,
    ProviderInventory,
    ProviderProjectRecord,
    ProviderServiceRecord,
)
from aethos_core.providers.railway.inventory.railway_inventory_discovery import (
    RAILWAY_INVENTORY_PROBE,
    fetch_railway_inventory_topology,
    topology_to_inventory_summary,
)
from aethos_core.providers.railway.mutations import resolve_railway_mutation_credentials
from aethos_core.security.secret_redaction import redact_text

_log = logging.getLogger(__name__)

_MAX_DEPLOYMENT_HEALTH_ENRICH = 50


def _latest_deployment_for_service(
    token: str,
    service_id: str,
) -> tuple[ProviderDeploymentRecord | None, str, str, str | None]:
    from aethos_core.operational_planner.adapters.railway_wide_health import _classify_status_and_health
    from aethos_core.providers.railway.api_client import list_service_deployments

    sid = (service_id or "").strip()
    if not sid:
        return None, "unknown", "unknown", "missing_service_id"
    try:
        deployments = list_service_deployments(token, service_id=sid, limit=1)
    except Exception as exc:
        return None, "unknown", "unknown", f"deployment_lookup_failed:{redact_text(str(exc))[:80]}"
    if not deployments:
        return None, "unknown", "unknown", "no_deployments"
    latest = deployments[0]
    dep_state = str(latest.get("state") or "unknown")
    dep = ProviderDeploymentRecord(
        id=str(latest.get("id") or ""),
        status=dep_state,
        created_at=latest.get("created_at"),
        url=latest.get("url"),
    )
    status, health = _classify_status_and_health("", dep_state)
    return dep, status, health, None


def _infer_service_type(name: str) -> str:
    norm = (name or "").strip().lower()
    if any(token in norm for token in ("postgres", "postgresql", "mysql", "redis", "mongo")):
        return "database"
    if "worker" in norm or "queue" in norm or "job" in norm:
        return "worker"
    if "scheduler" in norm or "cron" in norm:
        return "scheduler"
    if "bot" in norm:
        return "bot"
    if "web" in norm:
        return "web"
    return "web"


def _service_aliases(*, project_name: str, service_name: str) -> list[str]:
    aliases = [service_name, f"{project_name} {service_name}", f"{project_name}-{service_name}"]
    return list(dict.fromkeys(a for a in aliases if a))


def _execution_mode() -> str:
    mode = (get_settings().railway_execution_mode or "api").strip().lower()
    return mode if mode in {"cli", "api"} else "api"


def safe_discover_railway_inventory() -> ProviderInventory:
    """Discover Railway inventory without raising — provider-safe boundary."""
    try:
        return discover_railway_inventory()
    except Exception as exc:
        _log.exception("Railway inventory discovery failed")
        now = datetime.now(UTC).isoformat()
        return ProviderInventory(
            provider="railway",
            last_refreshed_at=now,
            freshness="failed",
            execution_mode=_execution_mode(),
            error=redact_text(str(exc))[:240],
            evidence={"inventory_probe": RAILWAY_INVENTORY_PROBE, "failure_class": type(exc).__name__},
        )


def discover_railway_inventory() -> ProviderInventory:
    mode = _execution_mode()
    if mode == "cli":
        return _discover_via_cli()
    return _discover_via_api()


def refresh_railway_inventory(*, force: bool = False) -> ProviderInventory:
    _ = force
    return discover_railway_inventory()


def list_railway_projects() -> list[dict[str, Any]]:
    inventory = safe_discover_railway_inventory()
    return [{"id": p.id, "name": p.name} for p in inventory.projects]


def list_railway_environments(project_id: str) -> list[dict[str, Any]]:
    inventory = safe_discover_railway_inventory()
    for project in inventory.projects:
        if project.id == project_id:
            return [{"id": env.id, "name": env.name} for env in project.environments]
    return []


def list_railway_services(project_id: str, environment_id: str) -> list[dict[str, Any]]:
    inventory = safe_discover_railway_inventory()
    for project in inventory.projects:
        if project.id != project_id:
            continue
        for environment in project.environments:
            if environment.id != environment_id:
                continue
            return [svc.to_dict() for svc in environment.services]
    return []


def list_railway_deployments(service_id: str, environment_id: str | None = None) -> list[dict[str, Any]]:
    _ = environment_id
    token, _, _ = resolve_railway_mutation_credentials()
    if not token:
        return []
    from aethos_core.providers.railway.api_client import list_service_deployments

    return list_service_deployments(token, service_id=service_id, limit=10)


def list_railway_domains(service_id: str, environment_id: str | None = None) -> list[str]:
    deployments = list_railway_deployments(service_id, environment_id)
    domains: list[str] = []
    for row in deployments:
        url = str(row.get("url") or "").strip()
        if url and url not in domains:
            domains.append(url)
    return domains


def list_railway_variables(service_id: str, environment_id: str | None = None) -> dict[str, Any]:
    _ = environment_id
    inventory = safe_discover_railway_inventory()
    row = inventory.find_service_by_id(service_id)
    if not row:
        return {"ok": False, "variables": [], "error": "service_not_found"}
    mode = _execution_mode()
    if mode == "cli":
        from aethos_core.providers.railway.cli_executor import railway_variables

        return railway_variables(service_name=str(row.get("service_name") or ""))
    token, _, cred_error = resolve_railway_mutation_credentials()
    if not token:
        return {"ok": False, "variables": [], "error": cred_error or "missing credentials"}
    return {"ok": True, "variables": [], "detail": "Variable metadata available via CLI mode or future API mapping."}


def _discover_via_api() -> ProviderInventory:
    token, source, cred_error = resolve_railway_mutation_credentials()
    now = datetime.now(UTC).isoformat()
    if not token:
        return ProviderInventory(
            provider="railway",
            last_refreshed_at=now,
            freshness="unavailable",
            execution_mode="api",
            error=cred_error or "Railway credentials missing.",
            evidence={"credential_source": source, "inventory_probe": RAILWAY_INVENTORY_PROBE},
        )

    from aethos_core.providers.railway.credential_truth import validate_railway_api_connection

    connection = validate_railway_api_connection(token)
    if not connection.ok:
        return ProviderInventory(
            provider="railway",
            last_refreshed_at=now,
            freshness="failed",
            execution_mode="api",
            error=connection.detail,
            evidence={
                "credential_source": source,
                "validation_probe": connection.probe,
                "inventory_probe": RAILWAY_INVENTORY_PROBE,
                "inventory_probe_status": "skipped_token_invalid",
            },
        )

    topology = fetch_railway_inventory_topology(token)
    if not topology.ok:
        return ProviderInventory(
            provider="railway",
            last_refreshed_at=now,
            freshness="failed",
            execution_mode="api",
            error=topology.error,
            evidence={
                "credential_source": source,
                "validation_probe": connection.probe,
                "inventory_probe": topology.probe,
                "inventory_probe_status": "fail",
                "graphql_errors": topology.graphql_errors,
            },
        )

    workspace = "railway"
    projects: list[ProviderProjectRecord] = []
    for project_row in topology.projects:
        project_id = str(project_row.get("id") or "")
        project_name = str(project_row.get("name") or project_id)
        environments: list[ProviderEnvironmentRecord] = []
        for env_row in list(project_row.get("environments") or []):
            env_id = str(env_row.get("id") or "")
            env_name = str(env_row.get("name") or env_id or "production")
            services: list[ProviderServiceRecord] = []
            enrich_count = 0
            for svc_row in list(env_row.get("services") or []):
                service_id = str(svc_row.get("id") or "")
                service_name = str(svc_row.get("name") or "")
                if not service_name:
                    continue
                service_type = _infer_service_type(service_name)
                latest_dep: ProviderDeploymentRecord | None = None
                svc_status = "unknown"
                if enrich_count < _MAX_DEPLOYMENT_HEALTH_ENRICH and service_id:
                    latest_dep, svc_status, _, _ = _latest_deployment_for_service(token, service_id)
                    enrich_count += 1
                services.append(
                    ProviderServiceRecord(
                        name=service_name,
                        id=service_id,
                        type=service_type,
                        status=svc_status,
                        domain=latest_dep.url if latest_dep and latest_dep.url else None,
                        aliases=_service_aliases(project_name=project_name, service_name=service_name),
                        latest_deployment=latest_dep,
                        supported_operations=service_supported_operations(provider="railway", service_type=service_type),
                        variables_available=True,
                        logs_available=True,
                    )
                )
            environments.append(ProviderEnvironmentRecord(name=env_name, id=env_id, services=services))
        projects.append(ProviderProjectRecord(name=project_name, id=project_id, environments=environments))

    summary = topology_to_inventory_summary(topology)
    return ProviderInventory(
        provider="railway",
        workspace=workspace,
        projects=projects,
        last_refreshed_at=now,
        freshness="fresh",
        execution_mode="api",
        error="",
        evidence={
            "credential_source": source,
            "validation_probe": connection.probe,
            "inventory_probe": topology.probe,
            "inventory_probe_status": "pass",
            "inventory_summary": summary,
        },
    )


def _discover_via_cli() -> ProviderInventory:
    from aethos_core.providers.railway.cli_executor import railway_status

    now = datetime.now(UTC).isoformat()
    status = railway_status()
    if not status.get("ok"):
        return ProviderInventory(
            provider="railway",
            last_refreshed_at=now,
            freshness="failed",
            execution_mode="cli",
            error=str(status.get("error") or "Railway CLI status failed."),
            evidence={"cli": status, "inventory_probe": RAILWAY_INVENTORY_PROBE},
        )
    parsed = status.get("parsed")
    if isinstance(parsed, dict):
        api_inventory = _discover_via_api()
        if api_inventory.projects:
            api_inventory.execution_mode = "cli"
            api_inventory.evidence = {**api_inventory.evidence, "cli_status": status}
            return api_inventory
    return _discover_via_api()
