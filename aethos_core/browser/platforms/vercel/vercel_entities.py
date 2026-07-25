# SPDX-License-Identifier: Apache-2.0
"""Vercel operational entities — how AethOS thinks about infrastructure state."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from time import time
from typing import Any


class HealthState(str, Enum):
    HEALTHY = "healthy"
    LIKELY_HEALTHY = "likely_healthy"
    UNKNOWN = "unknown"
    LIKELY_DEGRADED = "likely_degraded"
    DEGRADED = "degraded"
    FAILED = "failed"


@dataclass
class VercelProject:
    name: str
    status: str = "active"
    health: HealthState = HealthState.UNKNOWN
    deployment_status: str | None = None
    production_url: str | None = None
    git_repo: str | None = None
    last_deployment: str | None = None
    last_deploy_state: str | None = None
    deployment_state: str | None = None
    attention_reason: str | None = None
    environment: str | None = None
    production_url_source: str | None = None
    production_url_confidence: str = "none"
    production_url_verified: bool = False
    known_domains: list[str] = field(default_factory=list)
    health_confidence: str | None = None
    url_type: str = "unknown"
    production_health: str = "unknown"
    latest_deployment_state: str = "unknown"
    latest_deployment_scope: str = "unknown"
    operator_status: str = "unknown"
    evidence: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status,
            "health": self.health.value,
            "health_confidence": self.health_confidence or self.health.value,
            "deployment_status": self.deployment_status,
            "production_url": self.production_url,
            "production_url_source": self.production_url_source,
            "production_url_confidence": self.production_url_confidence,
            "production_url_verified": self.production_url_verified,
            "known_domains": list(self.known_domains),
            "git_repo": self.git_repo,
            "last_deployment": self.last_deployment,
            "last_deploy_state": self.last_deploy_state,
            "deployment_state": self.deployment_state,
            "attention_reason": self.attention_reason,
            "environment": self.environment,
            "url_type": self.url_type,
            "production_health": self.production_health,
            "latest_deployment_state": self.latest_deployment_state,
            "latest_deployment_scope": self.latest_deployment_scope,
            "operator_status": self.operator_status,
            "evidence": list(self.evidence),
        }


@dataclass
class InfrastructureHealthSummary:
    healthy: list[str] = field(default_factory=list)
    likely_healthy: list[str] = field(default_factory=list)
    degraded: list[str] = field(default_factory=list)
    likely_degraded: list[str] = field(default_factory=list)
    failed: list[str] = field(default_factory=list)
    unknown: list[str] = field(default_factory=list)
    needs_attention: list[tuple[str, str]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "healthy": self.healthy,
            "likely_healthy": self.likely_healthy,
            "degraded": self.degraded,
            "likely_degraded": self.likely_degraded,
            "failed": self.failed,
            "unknown": self.unknown,
            "needs_attention": [{"name": n, "reason": r} for n, r in self.needs_attention],
        }


@dataclass
class VercelInventoryArtifact:
    projects: list[VercelProject] = field(default_factory=list)
    health_summary: InfrastructureHealthSummary = field(default_factory=InfrastructureHealthSummary)
    healthy_count: int = 0
    failing_count: int = 0
    no_prod_count: int = 0
    degraded_count: int = 0
    unknown_count: int = 0
    extracted_at: float = field(default_factory=time)
    extraction_method: str = "dom_semantic"
    ignored_labels: list[str] = field(default_factory=list)
    low_confidence_count: int = 0
    likely_project_names: list[str] = field(default_factory=list)
    memory_fallback: bool = False
    extraction_debug: dict[str, Any] | None = None
    memory_delta: dict[str, list[str]] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "projects": [p.to_dict() for p in self.projects],
            "health_summary": self.health_summary.to_dict(),
            "healthy_count": self.healthy_count,
            "failing_count": self.failing_count,
            "no_prod_count": self.no_prod_count,
            "degraded_count": self.degraded_count,
            "unknown_count": self.unknown_count,
            "extracted_at": self.extracted_at,
            "extraction_method": self.extraction_method,
            "project_count": len(self.projects),
            "ignored_labels": self.ignored_labels,
            "low_confidence_count": self.low_confidence_count,
            "likely_project_names": self.likely_project_names,
            "memory_fallback": self.memory_fallback,
            "extraction_debug": self.extraction_debug,
            "memory_delta": self.memory_delta,
        }
