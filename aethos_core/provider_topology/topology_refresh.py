# SPDX-License-Identifier: Apache-2.0
"""Refresh provider topology graph from inventory and bindings."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from aethos_core.provider_topology.source_binding import SourceBinding
from aethos_core.provider_topology.topology_graph import ProviderTopologyGraph
from aethos_core.provider_topology.topology_memory import cache_graph, get_binding, save_binding


def refresh_service_topology(
    *,
    provider: str,
    project: str,
    environment: str,
    service_name: str,
    github_repo: str | None = None,
    force: bool = False,
) -> ProviderTopologyGraph | None:
    from aethos_core.provider_topology.provider_relationships import build_topology_graph

    binding = get_binding(provider=provider, project=project, environment=environment, service_name=service_name)
    if binding is None:
        binding = _binding_from_inventory(provider=provider, project=project, environment=environment, service_name=service_name)
    if binding is None:
        return None

    if github_repo and (force or not binding.github_repo or binding.github_repo.lower() != github_repo.lower()):
        binding.github_repo = github_repo
        if not force:
            binding.source_verified = False

    deployments = _deployments_from_inventory(provider=provider, project=project, environment=environment, service_name=service_name)
    binding.updated_at = datetime.now(UTC).isoformat()
    save_binding(binding)
    graph = build_topology_graph(binding, deployments=deployments)
    graph.updated_at = binding.updated_at
    cache_graph(graph)
    return graph


def _binding_from_inventory(*, provider: str, project: str, environment: str, service_name: str) -> SourceBinding | None:
    try:
        from aethos_core.provider_discovery import get_provider_inventory

        inventory = get_provider_inventory(provider)
        if inventory is None:
            return None
        for row in inventory.all_services():
            if (
                str(row.get("project_name") or "") == project
                and str(row.get("environment") or "production") == environment
                and str(row.get("service_name") or "") == service_name
            ):
                return SourceBinding(
                    provider=provider,
                    project=project,
                    environment=environment,
                    service_name=service_name,
                    service_id=str(row.get("service_id") or ""),
                    domains=[str(row.get("domain"))] if row.get("domain") else [],
                    updated_at=datetime.now(UTC).isoformat(),
                )
    except Exception:
        return None
    return None


def _deployments_from_inventory(*, provider: str, project: str, environment: str, service_name: str) -> list[dict[str, Any]]:
    try:
        from aethos_core.provider_discovery import get_provider_inventory

        inventory = get_provider_inventory(provider)
        if inventory is None:
            return []
        for row in inventory.all_services():
            if (
                str(row.get("project_name") or "") == project
                and str(row.get("environment") or "production") == environment
                and str(row.get("service_name") or "") == service_name
            ):
                dep = row.get("latest_deployment")
                if isinstance(dep, dict) and dep.get("id"):
                    return [
                        {
                            "provider": provider,
                            "deployment_id": dep.get("id"),
                            "status": dep.get("status"),
                            "url": dep.get("url"),
                        }
                    ]
    except Exception:
        return []
    return []


def refresh_topology_on_failure(
    *,
    provider: str,
    project: str,
    environment: str,
    service_name: str,
    failure_reason: str,
    referenced_repo: str | None = None,
) -> ProviderTopologyGraph | None:
    force = any(
        token in (failure_reason or "").lower()
        for token in ("installation", "repo", "binding", "github", "source mismatch", "not found")
    )
    return refresh_service_topology(
        provider=provider,
        project=project,
        environment=environment,
        service_name=service_name,
        github_repo=referenced_repo,
        force=force,
    )
