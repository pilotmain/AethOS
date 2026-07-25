# SPDX-License-Identifier: Apache-2.0
"""Unified provider topology graph model."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ServiceNode:
    provider: str
    project: str
    environment: str
    service_name: str
    service_id: str | None = None
    status: str = "unknown"
    domain: str | None = None

    def path(self) -> str:
        return f"{self.project} / {self.environment} / {self.service_name}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "project": self.project,
            "environment": self.environment,
            "service_name": self.service_name,
            "service_id": self.service_id,
            "status": self.status,
            "domain": self.domain,
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> ServiceNode:
        return cls(
            provider=str(raw.get("provider") or "railway"),
            project=str(raw.get("project") or raw.get("project_name") or ""),
            environment=str(raw.get("environment") or "production"),
            service_name=str(raw.get("service_name") or raw.get("service") or raw.get("name") or ""),
            service_id=raw.get("service_id"),
            status=str(raw.get("status") or "unknown"),
            domain=raw.get("domain"),
        )


@dataclass
class SourceNode:
    provider: str = "github"
    repo: str = ""
    installation_id: str | None = None
    branch: str | None = None
    verified: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "repo": self.repo,
            "installation_id": self.installation_id,
            "branch": self.branch,
            "verified": self.verified,
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> SourceNode:
        return cls(
            provider=str(raw.get("provider") or "github"),
            repo=str(raw.get("repo") or ""),
            installation_id=raw.get("installation_id"),
            branch=raw.get("branch"),
            verified=bool(raw.get("verified", False)),
        )


@dataclass
class DeploymentNode:
    provider: str
    deployment_id: str
    status: str = "unknown"
    url: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "deployment_id": self.deployment_id,
            "status": self.status,
            "url": self.url,
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> DeploymentNode:
        return cls(
            provider=str(raw.get("provider") or "railway"),
            deployment_id=str(raw.get("deployment_id") or raw.get("id") or ""),
            status=str(raw.get("status") or "unknown"),
            url=raw.get("url"),
        )


@dataclass
class ProviderTopologyGraph:
    service: ServiceNode
    source: SourceNode | None = None
    deployments: list[DeploymentNode] = field(default_factory=list)
    domains: list[str] = field(default_factory=list)
    binding_key: str = ""
    updated_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "service": self.service.to_dict(),
            "source": self.source.to_dict() if self.source else None,
            "deployments": [d.to_dict() for d in self.deployments],
            "domains": list(self.domains),
            "binding_key": self.binding_key,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> ProviderTopologyGraph:
        service_raw = raw.get("service") or {}
        source_raw = raw.get("source")
        return cls(
            service=ServiceNode.from_dict(service_raw if isinstance(service_raw, dict) else {}),
            source=SourceNode.from_dict(source_raw) if isinstance(source_raw, dict) else None,
            deployments=[DeploymentNode.from_dict(row) for row in (raw.get("deployments") or []) if isinstance(row, dict)],
            domains=[str(d) for d in (raw.get("domains") or [])],
            binding_key=str(raw.get("binding_key") or ""),
            updated_at=str(raw.get("updated_at") or ""),
        )
