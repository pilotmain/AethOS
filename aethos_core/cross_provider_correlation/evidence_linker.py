# SPDX-License-Identifier: Apache-2.0
"""Link provider evidence into a correlation graph."""

from __future__ import annotations

from typing import Any

from aethos_core.cross_provider_correlation.commit_identity import commits_match, normalize_repo, repos_match
from aethos_core.cross_provider_correlation.correlation_graph import CorrelationGraph, CorrelationLink
from aethos_core.cross_provider_correlation.deployment_identity import DeploymentIdentity
from aethos_core.cross_provider_correlation.provider_identity import ProviderIdentity


def link_cross_provider_evidence(
    snapshot: dict[str, Any],
    *,
    session_id: str = "default",
) -> CorrelationGraph:
    github = ProviderIdentity.from_dict(snapshot.get("github"))
    vercel = DeploymentIdentity.from_dict(snapshot.get("vercel"))
    railway = DeploymentIdentity.from_dict(snapshot.get("railway"))
    links: list[CorrelationLink] = []
    matched_commit = ""

    bindings = _load_bindings()
    if github and vercel and commits_match(github.commit_sha, vercel.commit_sha):
        matched_commit = github.commit_sha or vercel.commit_sha
        links.append(
            CorrelationLink(
                kind="commit_sha",
                source="github",
                target="vercel",
                confidence=0.95,
                detail=f"Matched commit `{matched_commit[:12]}`",
            )
        )
    if github and vercel:
        repo_link = str((vercel.metadata or {}).get("repo_link") or "")
        if repo_link and repos_match(github.repo, repo_link):
            links.append(
                CorrelationLink(
                    kind="repo",
                    source="github",
                    target="vercel",
                    confidence=0.9,
                    detail=f"Repo `{normalize_repo(github.repo)}` linked to Vercel project `{vercel.project}`",
                )
            )
    if vercel and railway and commits_match(vercel.commit_sha, railway.commit_sha):
        if not matched_commit:
            matched_commit = vercel.commit_sha or railway.commit_sha
        links.append(
            CorrelationLink(
                kind="commit_sha",
                source="vercel",
                target="railway",
                confidence=0.85,
                detail=f"Matched commit `{matched_commit[:12]}`",
            )
        )
    if github and railway and commits_match(github.commit_sha, railway.commit_sha):
        if not matched_commit:
            matched_commit = github.commit_sha or railway.commit_sha
        links.append(
            CorrelationLink(
                kind="commit_sha",
                source="github",
                target="railway",
                confidence=0.85,
                detail=f"Matched commit `{matched_commit[:12]}`",
            )
        )

    for binding in bindings:
        if github and binding.github_repo and repos_match(github.repo, binding.github_repo):
            if vercel and binding.vercel_project and vercel.project.lower() == binding.vercel_project.lower():
                links.append(
                    CorrelationLink(
                        kind="binding",
                        source="github",
                        target="vercel",
                        confidence=0.8,
                        detail=f"Topology binding links `{binding.github_repo}` → `{binding.vercel_project}`",
                    )
                )
            if railway and binding.service_name and railway.service.lower() == binding.service_name.lower():
                links.append(
                    CorrelationLink(
                        kind="binding",
                        source="github",
                        target="railway",
                        confidence=0.75,
                        detail=f"Topology binding links `{binding.github_repo}` → `{binding.service_name}`",
                    )
                )

    confidence = _graph_confidence(links, github, vercel, railway)
    return CorrelationGraph(
        session_id=session_id,
        github=github,
        vercel=vercel,
        railway=railway,
        links=links,
        confidence=confidence,
        matched_commit=matched_commit,
    )


def _load_bindings() -> list[Any]:
    try:
        from aethos_core.provider_topology.topology_memory import load_all_bindings

        return list(load_all_bindings().values())
    except Exception:
        return []


def _graph_confidence(
    links: list[CorrelationLink],
    github: ProviderIdentity | None,
    vercel: DeploymentIdentity | None,
    railway: DeploymentIdentity | None,
) -> str:
    if not links:
        if not github and not vercel and not railway:
            return "insufficient"
        return "low"
    high = [link for link in links if link.confidence >= 0.85]
    if len(high) >= 2:
        return "high"
    if links:
        return "moderate"
    return "low"
