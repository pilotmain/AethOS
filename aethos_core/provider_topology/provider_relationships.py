# SPDX-License-Identifier: Apache-2.0
"""Cross-provider relationship helpers — Railway ↔ GitHub ↔ Vercel."""

from __future__ import annotations

import re
from typing import Any

from aethos_core.provider_topology.source_binding import SourceBinding
from aethos_core.provider_topology.topology_graph import DeploymentNode, ProviderTopologyGraph, ServiceNode, SourceNode

_GITHUB_REPO_RX = re.compile(
    r"\b(?:github\.com/|https?://github\.com/)?"
    r"([a-z0-9][a-z0-9._-]*/[a-z0-9][a-z0-9._-]+)\b",
    re.I,
)


def extract_github_repo_references(text: str) -> list[str]:
    refs: list[str] = []
    seen: set[str] = set()
    for match in _GITHUB_REPO_RX.finditer(text or ""):
        repo = match.group(1).strip().lower()
        if repo not in seen:
            seen.add(repo)
            refs.append(match.group(1).strip())
    return refs


def build_topology_graph(binding: SourceBinding, *, deployments: list[dict[str, Any]] | None = None) -> ProviderTopologyGraph:
    service = ServiceNode(
        provider=binding.provider,
        project=binding.project,
        environment=binding.environment,
        service_name=binding.service_name,
        service_id=binding.service_id,
        domain=(binding.domains or [None])[0],
    )
    source = None
    if binding.github_repo:
        source = SourceNode(
            provider="github",
            repo=binding.github_repo,
            installation_id=binding.github_installation_id,
            verified=binding.source_verified,
        )
    dep_nodes = [
        DeploymentNode(
            provider=str(row.get("provider") or binding.provider),
            deployment_id=str(row.get("deployment_id") or row.get("id") or ""),
            status=str(row.get("status") or "unknown"),
            url=row.get("url"),
        )
        for row in (deployments or [])
        if isinstance(row, dict)
    ]
    return ProviderTopologyGraph(
        service=service,
        source=source,
        deployments=dep_nodes,
        domains=list(binding.domains or []),
        binding_key=binding.key,
        updated_at=binding.updated_at,
    )


def railway_github_relationship_summary(graph: ProviderTopologyGraph) -> str:
    svc = graph.service.path()
    repo = graph.source.repo if graph.source else "(none)"
    return f"Railway service **{svc}** ↔ GitHub repo **{repo}**"
