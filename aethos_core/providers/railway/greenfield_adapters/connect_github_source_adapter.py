# SPDX-License-Identifier: Apache-2.0
"""
FIX 109 — Governed GitHub source binding (connect_source phase only).

Binds repo/branch to an existing Railway service via environmentStageChanges +
environmentPatchCommitStaged(skipDeploys=true). No env writes, no deploy trigger.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from aethos_core.providers.railway.greenfield_adapters.greenfield_mutation_scope import (
    STAGING_ONLY_ENVIRONMENTS,
)
from aethos_core.providers.railway.greenfield_adapters.mutation_live_gate import (
    LiveMutationKillSwitchActiveError,
    LiveMutationModeError,
    LiveMutationNotAuthorizedError,
    require_live_connect_github_source_authorization,
)
from aethos_core.providers.railway.greenfield_adapters.source_bind_graphql import (
    commit_staged_changes_skip_deploy,
    stage_github_source_binding,
)
from aethos_core.providers.railway.greenfield_deployment.git_remote_resolution import (
    normalize_github_repository_slug,
)
from aethos_core.providers.railway.mutations import resolve_railway_mutation_credentials
from aethos_core.security.secret_redaction import redact_text


@dataclass(frozen=True)
class ConnectGithubSourceResult:
    ok: bool
    mutation_performed: bool = False
    idempotent_replay: bool = False
    service_id: str = ""
    environment_id: str = ""
    repository: str = ""
    branch: str = ""
    provider_request_id: str = ""
    detail: str = ""
    errors: list[str] = field(default_factory=list)


def _normalize_repo(repo: str) -> str:
    return normalize_github_repository_slug(repo)


def connect_github_source(
    *,
    environment_name: str,
    environment_id: str,
    service_id: str,
    repository: str,
    branch: str,
    idempotency_key: str,
    existing_binding: dict[str, str] | None = None,
    root_directory: str = "",
) -> ConnectGithubSourceResult:
    """
    Governed live connect_source mutation.

    Requires live_connect_github_source_authorization() from the real-mutation executor.
    """
    _ = idempotency_key
    try:
        require_live_connect_github_source_authorization()
    except (LiveMutationNotAuthorizedError, LiveMutationKillSwitchActiveError, LiveMutationModeError) as exc:
        return ConnectGithubSourceResult(ok=False, detail="", errors=[str(exc)])

    env_norm = (environment_name or "").strip().lower()
    if env_norm not in STAGING_ONLY_ENVIRONMENTS:
        return ConnectGithubSourceResult(
            ok=False,
            detail="",
            errors=[
                "FIX 109 GitHub source binding is limited to staging environments "
                f"({', '.join(sorted(STAGING_ONLY_ENVIRONMENTS))})."
            ],
        )

    repo = _normalize_repo(repository)
    branch_name = (branch or "main").strip()
    root = (root_directory or "").strip().strip("/")
    if not service_id:
        return ConnectGithubSourceResult(ok=False, detail="", errors=["service_id is required"])
    if not environment_id:
        return ConnectGithubSourceResult(ok=False, detail="", errors=["environment_id is required"])
    if not repo:
        return ConnectGithubSourceResult(ok=False, detail="", errors=["repository is required"])

    prior = existing_binding or {}
    if (
        prior.get("repository") == repo
        and prior.get("branch") == branch_name
        and str(prior.get("root_directory") or "") == root
    ):
        return ConnectGithubSourceResult(
            ok=True,
            mutation_performed=False,
            idempotent_replay=True,
            service_id=service_id,
            environment_id=environment_id,
            repository=repo,
            branch=branch_name,
            detail="GitHub source already bound for this execution; no mutation performed.",
        )

    token, source, cred_error = resolve_railway_mutation_credentials()
    if not token:
        return ConnectGithubSourceResult(
            ok=False,
            detail="",
            errors=[redact_text(cred_error or f"Railway credentials unavailable (source={source}).")],
        )

    stage_result: dict[str, Any] = stage_github_source_binding(
        token,
        environment_id=environment_id,
        service_id=service_id,
        repo=repo,
        branch=branch_name,
        root_directory=root,
    )
    if not stage_result.get("ok"):
        return ConnectGithubSourceResult(
            ok=False,
            service_id=service_id,
            environment_id=environment_id,
            repository=repo,
            branch=branch_name,
            detail="",
            errors=[redact_text(str(stage_result.get("detail") or "stage failed"))],
        )

    commit_result = commit_staged_changes_skip_deploy(token, environment_id=environment_id)
    if not commit_result.get("ok"):
        return ConnectGithubSourceResult(
            ok=False,
            service_id=service_id,
            environment_id=environment_id,
            repository=repo,
            branch=branch_name,
            detail="",
            errors=[redact_text(str(commit_result.get("detail") or "commit failed"))],
        )

    return ConnectGithubSourceResult(
        ok=True,
        mutation_performed=True,
        service_id=service_id,
        environment_id=environment_id,
        repository=repo,
        branch=branch_name,
        provider_request_id=f"railway:connect_source:{service_id}:{repo}@{branch_name}",
        detail="GitHub source bound via environmentStageChanges + commit (skipDeploys=true).",
    )
