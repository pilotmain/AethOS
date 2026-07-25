# SPDX-License-Identifier: Apache-2.0
"""Resolve GitHub repository targets via provider API."""

from __future__ import annotations

from aethos_core.operations.target_resolution import TargetResolution
from aethos_core.providers.github.auth import GitHubAuthAdapter


def resolve_github_target(
    *,
    user_request: str,
    target_hints: list[str] | None,
    operation_type: str,
) -> TargetResolution:
    from aethos_core.operations.orchestration.target_resolution.canonical_resolver import collect_target_hints

    hints = collect_target_hints(user_request=user_request, target_hints=target_hints)
    _ = operation_type
    auth = GitHubAuthAdapter().resolve_best_auth_method(operation="read_repos")
    if not auth.get("credential_id"):
        return TargetResolution(
            status="missing",
            target_name=hints[0] if hints else None,
            message="No GitHub API token configured.",
            source="provider_api",
        )
    from aethos_core.providers.github.api_client import find_repository_by_name, list_repositories

    token = GitHubAuthAdapter().get_api_token(str(auth["credential_id"]))
    listed = list_repositories(token)
    if not listed.get("ok"):
        return TargetResolution(
            status="missing",
            target_name=hints[0] if hints else None,
            message=str(listed.get("error") or "GitHub repository list failed."),
            source="provider_api",
        )
    repos = listed.get("repositories") or []
    names = [str(r.get("full_name") or r.get("name") or "") for r in repos if isinstance(r, dict)]
    if not hints:
        if len(names) == 1:
            return TargetResolution(status="resolved", target_name=names[0], source="provider_api")
        return TargetResolution(
            status="missing",
            matches=names[:8],
            message="Specify a GitHub repository name or owner/repo.",
            source="provider_api",
        )
    primary = hints[0]
    matched = find_repository_by_name(token, primary)
    if matched:
        full_name = str(matched.get("full_name") or "")
        if full_name:
            return TargetResolution(status="resolved", target_name=full_name, source="provider_api")
    partial = [
        n
        for n in names
        if primary.lower() in n.lower() or n.split("/")[-1].lower() == primary.lower()
    ]
    if len(partial) == 1:
        return TargetResolution(status="resolved", target_name=partial[0], source="provider_api")
    if len(partial) > 1:
        return TargetResolution(
            status="ambiguous",
            matches=partial[:8],
            message="Multiple GitHub repositories matched.",
            source="provider_api",
        )
    return TargetResolution(
        status="missing",
        target_name=primary,
        matches=names[:8],
        message=f"Repository `{primary}` not found in GitHub account.",
        source="provider_api",
    )
