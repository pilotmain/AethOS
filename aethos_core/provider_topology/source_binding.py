# SPDX-License-Identifier: Apache-2.0
"""Service ↔ source repository binding records."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


def binding_key(*, provider: str, project: str, environment: str, service_name: str) -> str:
    return f"{provider}:{project}:{environment}:{service_name}".lower()


@dataclass
class SourceBinding:
    provider: str
    project: str
    environment: str
    service_name: str
    service_id: str | None = None
    github_repo: str | None = None
    github_installation_id: str | None = None
    vercel_project: str | None = None
    domains: list[str] | None = None
    source_verified: bool = False
    updated_at: str = ""

    @property
    def key(self) -> str:
        return binding_key(
            provider=self.provider,
            project=self.project,
            environment=self.environment,
            service_name=self.service_name,
        )

    def service_path(self) -> str:
        return f"{self.project} / {self.environment} / {self.service_name}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "project": self.project,
            "environment": self.environment,
            "service_name": self.service_name,
            "service_id": self.service_id,
            "github_repo": self.github_repo,
            "github_installation_id": self.github_installation_id,
            "vercel_project": self.vercel_project,
            "domains": list(self.domains or []),
            "source_verified": self.source_verified,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> SourceBinding:
        return cls(
            provider=str(raw.get("provider") or "railway"),
            project=str(raw.get("project") or raw.get("project_name") or ""),
            environment=str(raw.get("environment") or "production"),
            service_name=str(raw.get("service_name") or raw.get("service") or ""),
            service_id=raw.get("service_id"),
            github_repo=raw.get("github_repo"),
            github_installation_id=raw.get("github_installation_id"),
            vercel_project=raw.get("vercel_project"),
            domains=[str(d) for d in (raw.get("domains") or [])],
            source_verified=bool(raw.get("source_verified", False)),
            updated_at=str(raw.get("updated_at") or ""),
        )
