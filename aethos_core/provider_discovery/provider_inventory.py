# SPDX-License-Identifier: Apache-2.0
"""Provider inventory model — workspace topology snapshots."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ProviderDeploymentRecord:
    id: str
    status: str = "unknown"
    created_at: str | None = None
    url: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "status": self.status,
            "created_at": self.created_at,
            "url": self.url,
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> ProviderDeploymentRecord:
        return cls(
            id=str(raw.get("id") or ""),
            status=str(raw.get("status") or raw.get("state") or "unknown"),
            created_at=raw.get("created_at"),
            url=raw.get("url"),
        )


@dataclass
class ProviderServiceRecord:
    name: str
    id: str
    type: str = "web"
    status: str = "unknown"
    domain: str | None = None
    aliases: list[str] = field(default_factory=list)
    latest_deployment: ProviderDeploymentRecord | None = None
    supported_operations: list[str] = field(default_factory=list)
    variables_available: bool = False
    logs_available: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "id": self.id,
            "type": self.type,
            "status": self.status,
            "domain": self.domain,
            "aliases": list(self.aliases),
            "latest_deployment": self.latest_deployment.to_dict() if self.latest_deployment else None,
            "supported_operations": list(self.supported_operations),
            "variables_available": self.variables_available,
            "logs_available": self.logs_available,
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> ProviderServiceRecord:
        dep_raw = raw.get("latest_deployment")
        dep = ProviderDeploymentRecord.from_dict(dep_raw) if isinstance(dep_raw, dict) else None
        return cls(
            name=str(raw.get("name") or ""),
            id=str(raw.get("id") or raw.get("service_id") or ""),
            type=str(raw.get("type") or "web"),
            status=str(raw.get("status") or "unknown"),
            domain=raw.get("domain"),
            aliases=[str(a) for a in (raw.get("aliases") or [])],
            latest_deployment=dep,
            supported_operations=[str(op) for op in (raw.get("supported_operations") or [])],
            variables_available=bool(raw.get("variables_available", False)),
            logs_available=bool(raw.get("logs_available", True)),
        )


@dataclass
class ProviderEnvironmentRecord:
    name: str
    id: str
    services: list[ProviderServiceRecord] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "id": self.id,
            "services": [svc.to_dict() for svc in self.services],
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> ProviderEnvironmentRecord:
        services = [ProviderServiceRecord.from_dict(row) for row in (raw.get("services") or []) if isinstance(row, dict)]
        return cls(name=str(raw.get("name") or ""), id=str(raw.get("id") or ""), services=services)


@dataclass
class ProviderProjectRecord:
    name: str
    id: str
    environments: list[ProviderEnvironmentRecord] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "id": self.id,
            "environments": [env.to_dict() for env in self.environments],
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> ProviderProjectRecord:
        envs = [ProviderEnvironmentRecord.from_dict(row) for row in (raw.get("environments") or []) if isinstance(row, dict)]
        return cls(name=str(raw.get("name") or ""), id=str(raw.get("id") or ""), environments=envs)


@dataclass
class ProviderInventory:
    provider: str
    workspace: str | None = None
    projects: list[ProviderProjectRecord] = field(default_factory=list)
    last_refreshed_at: str | None = None
    freshness: str = "unknown"
    execution_mode: str = "api"
    error: str | None = None
    evidence: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "workspace": self.workspace,
            "projects": [project.to_dict() for project in self.projects],
            "last_refreshed_at": self.last_refreshed_at,
            "freshness": self.freshness,
            "execution_mode": self.execution_mode,
            "error": self.error,
            "evidence": dict(self.evidence),
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> ProviderInventory:
        projects = [ProviderProjectRecord.from_dict(row) for row in (raw.get("projects") or []) if isinstance(row, dict)]
        return cls(
            provider=str(raw.get("provider") or ""),
            workspace=raw.get("workspace"),
            projects=projects,
            last_refreshed_at=raw.get("last_refreshed_at"),
            freshness=str(raw.get("freshness") or "unknown"),
            execution_mode=str(raw.get("execution_mode") or "api"),
            error=raw.get("error"),
            evidence=dict(raw.get("evidence") or {}),
        )

    def all_services(self) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for project in self.projects:
            for environment in project.environments:
                for service in environment.services:
                    rows.append(
                        {
                            "provider": self.provider,
                            "project_name": project.name,
                            "project_id": project.id,
                            "environment": environment.name,
                            "environment_id": environment.id,
                            "service_name": service.name,
                            "service_id": service.id,
                            "type": service.type,
                            "status": service.status,
                            "domain": service.domain,
                            "aliases": list(service.aliases),
                            "latest_deployment": service.latest_deployment.to_dict() if service.latest_deployment else None,
                            "supported_operations": list(service.supported_operations),
                        }
                    )
        return rows

    def find_service_by_id(self, service_id: str) -> dict[str, Any] | None:
        sid = (service_id or "").strip()
        for row in self.all_services():
            if str(row.get("service_id") or "") == sid:
                return row
        return None
