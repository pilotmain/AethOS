# SPDX-License-Identifier: Apache-2.0
"""Cross-provider correlation graph."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from aethos_core.cross_provider_correlation.deployment_identity import DeploymentIdentity
from aethos_core.cross_provider_correlation.provider_identity import ProviderIdentity


@dataclass
class CorrelationLink:
    kind: str
    source: str
    target: str
    confidence: float = 0.5
    detail: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "source": self.source,
            "target": self.target,
            "confidence": self.confidence,
            "detail": self.detail,
        }


@dataclass
class CorrelationGraph:
    session_id: str
    github: ProviderIdentity | None = None
    vercel: DeploymentIdentity | None = None
    railway: DeploymentIdentity | None = None
    links: list[CorrelationLink] = field(default_factory=list)
    failure_boundary: str = "unknown"
    confidence: str = "low"
    matched_commit: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "github": self.github.to_dict() if self.github else None,
            "vercel": self.vercel.to_dict() if self.vercel else None,
            "railway": self.railway.to_dict() if self.railway else None,
            "links": [link.to_dict() for link in self.links],
            "failure_boundary": self.failure_boundary,
            "confidence": self.confidence,
            "matched_commit": self.matched_commit,
        }
