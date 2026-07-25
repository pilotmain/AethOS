# SPDX-License-Identifier: Apache-2.0
"""Vercel/Railway deployment and runtime identity."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class DeploymentIdentity:
    provider: str
    project: str = ""
    service: str = ""
    environment: str = ""
    deployment_id: str = ""
    commit_sha: str = ""
    branch: str = ""
    domain: str = ""
    status: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "project": self.project,
            "service": self.service,
            "environment": self.environment,
            "deployment_id": self.deployment_id,
            "commit_sha": self.commit_sha,
            "branch": self.branch,
            "domain": self.domain,
            "status": self.status,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any] | None) -> DeploymentIdentity | None:
        if not raw:
            return None
        return cls(
            provider=str(raw.get("provider") or ""),
            project=str(raw.get("project") or ""),
            service=str(raw.get("service") or ""),
            environment=str(raw.get("environment") or ""),
            deployment_id=str(raw.get("deployment_id") or ""),
            commit_sha=str(raw.get("commit_sha") or ""),
            branch=str(raw.get("branch") or ""),
            domain=str(raw.get("domain") or ""),
            status=str(raw.get("status") or ""),
            metadata=dict(raw.get("metadata") or {}),
        )
