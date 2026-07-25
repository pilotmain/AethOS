# SPDX-License-Identifier: Apache-2.0
"""Provider topology helpers — project/environment/service relationships."""

from __future__ import annotations

from typing import Any

from aethos_core.provider_discovery.provider_inventory import ProviderInventory


def flatten_inventory_topology(inventory: ProviderInventory) -> list[dict[str, Any]]:
    return inventory.all_services()


def format_service_path(*, project: str, environment: str, service: str) -> str:
    return f"{project} / {environment} / {service}"


def service_topology_key(row: dict[str, Any]) -> str:
    return format_service_path(
        project=str(row.get("project_name") or "unknown"),
        environment=str(row.get("environment") or "production"),
        service=str(row.get("service_name") or "unknown"),
    )


def group_services_by_project_environment(inventory: ProviderInventory) -> dict[str, dict[str, list[dict[str, Any]]]]:
    grouped: dict[str, dict[str, list[dict[str, Any]]]] = {}
    for row in inventory.all_services():
        project = str(row.get("project_name") or "unknown")
        environment = str(row.get("environment") or "production")
        grouped.setdefault(project, {}).setdefault(environment, []).append(row)
    return grouped
