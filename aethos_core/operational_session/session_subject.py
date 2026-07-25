# SPDX-License-Identifier: Apache-2.0
"""Active operational subject — provider, project, service, environment."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SessionSubject:
    provider: str = ""
    project: str = ""
    service: str = ""
    environment: str = ""
    vercel_project: str = ""
    repo: str = ""
    alias: str = ""
    target_id: str = ""
    services: list[str] = field(default_factory=list)
    subject_source: str = ""

    def path_label(self) -> str:
        if self.provider == "vercel" and (self.vercel_project or self.project):
            return f"vercel / {self.vercel_project or self.project}"
        if self.project and self.service:
            env = self.environment or "production"
            return f"{self.project} / {env} / {self.service}"
        if self.provider == "railway" and self.project and not self.service:
            env = self.environment or "production"
            return f"{self.project} / {env}"
        if self.project:
            return self.project
        if self.vercel_project:
            return self.vercel_project
        if self.alias:
            return self.alias
        if self.provider:
            return self.provider
        return ""

    def primary_service(self) -> str:
        if self.service:
            return self.service
        if self.services:
            return self.services[0]
        return ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "project": self.project,
            "service": self.service,
            "environment": self.environment,
            "vercel_project": self.vercel_project,
            "repo": self.repo,
            "alias": self.alias,
            "target_id": self.target_id,
            "services": list(self.services),
            "subject_source": self.subject_source,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any] | None) -> SessionSubject:
        if not payload:
            return cls()
        services = payload.get("services") or []
        return cls(
            provider=str(payload.get("provider") or ""),
            project=str(payload.get("project") or ""),
            service=str(payload.get("service") or ""),
            environment=str(payload.get("environment") or ""),
            vercel_project=str(payload.get("vercel_project") or ""),
            repo=str(payload.get("repo") or ""),
            alias=str(payload.get("alias") or ""),
            target_id=str(payload.get("target_id") or ""),
            services=[str(item) for item in services if item],
            subject_source=str(payload.get("subject_source") or ""),
        )


def format_inventory_subject_label(
    *,
    provider: str,
    project_count: int = 0,
    service_count: int = 0,
    environment_count: int = 0,
) -> str:
    prov = (provider or "").strip().lower()
    if prov == "railway":
        parts = [f"{project_count} projects"]
        if environment_count:
            parts.append(f"{environment_count} environments")
        if service_count:
            parts.append(f"{service_count} services")
        return f"railway / {' · '.join(parts)}"
    if prov == "vercel":
        return f"vercel / {project_count} projects"
    return f"{prov or 'unknown'} / inventory"


def inventory_session_subject(
    *,
    provider: str,
    project_count: int = 0,
    service_count: int = 0,
    environment_count: int = 0,
) -> SessionSubject:
    label = format_inventory_subject_label(
        provider=provider,
        project_count=project_count,
        service_count=service_count,
        environment_count=environment_count,
    )
    return SessionSubject(provider=(provider or "").strip().lower(), alias=label, subject_source="session")
