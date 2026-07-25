# SPDX-License-Identifier: Apache-2.0
"""Resolve Railway project/environment IDs for governed create_service mutations."""

from __future__ import annotations

from dataclasses import dataclass, field

from aethos_core.providers.railway.discovery import discover_railway_inventory


@dataclass(frozen=True)
class RailwayTargetResolution:
    ok: bool
    project_id: str = ""
    project_name: str = ""
    environment_id: str = ""
    environment_name: str = ""
    errors: list[str] = field(default_factory=list)


def _normalize_name(value: str) -> str:
    return (value or "").strip().lower()


def resolve_railway_create_targets(
    *,
    project_name: str,
    environment_name: str,
) -> RailwayTargetResolution:
    """Resolve project and environment IDs from discovery inventory (read-only)."""
    project_key = _normalize_name(project_name)
    environment_key = _normalize_name(environment_name)
    if not project_key:
        return RailwayTargetResolution(ok=False, errors=["project name is required"])
    if not environment_key:
        return RailwayTargetResolution(ok=False, errors=["environment name is required"])

    inventory = discover_railway_inventory()
    if inventory.error:
        return RailwayTargetResolution(ok=False, errors=[str(inventory.error)])

    for project in inventory.projects:
        if _normalize_name(project.name) != project_key:
            continue
        for environment in project.environments:
            if _normalize_name(environment.name) == environment_key:
                return RailwayTargetResolution(
                    ok=True,
                    project_id=str(project.id),
                    project_name=str(project.name),
                    environment_id=str(environment.id),
                    environment_name=str(environment.name),
                )
        return RailwayTargetResolution(
            ok=False,
            project_id=str(project.id),
            project_name=str(project.name),
            errors=[f"environment `{environment_name}` not found in project `{project.name}`"],
        )

    return RailwayTargetResolution(
        ok=False,
        errors=[f"project `{project_name}` not found in Railway inventory"],
    )


def service_name_exists_in_project(
    *,
    project_id: str,
    service_name: str,
) -> bool:
    """Return True when a service with the same name already exists on the project."""
    return find_service_in_project(project_id=project_id, service_name=service_name) is not None


def find_service_in_project(
    *,
    project_id: str,
    service_name: str,
    environment_name: str = "",
) -> dict[str, str] | None:
    """Return service id/name and environment id/name when a matching service exists."""
    target = (service_name or "").strip().lower()
    env_key = (environment_name or "").strip().lower()
    if not target or not project_id:
        return None
    inventory = discover_railway_inventory()
    for project in inventory.projects:
        if str(project.id) != str(project_id):
            continue
        for environment in project.environments:
            if env_key and _normalize_name(environment.name) != env_key:
                continue
            for service in environment.services:
                if (service.name or "").strip().lower() != target:
                    continue
                return {
                    "service_id": str(service.id or ""),
                    "service_name": str(service.name or service_name),
                    "environment_id": str(environment.id or ""),
                    "environment_name": str(environment.name or ""),
                    "project_id": str(project.id or ""),
                    "project_name": str(project.name or ""),
                }
        break
    return None
