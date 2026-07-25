# SPDX-License-Identifier: Apache-2.0
"""
FIX 111 — Governed GitHub source disconnect (rollback_connect_source / disconnect_repo_source).

Clears repo binding via environmentStageChanges + environmentPatchCommitStaged(skipDeploys=true).
No env writes, no deploy trigger.
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
    require_live_disconnect_github_source_authorization,
)
from aethos_core.providers.railway.greenfield_adapters.source_bind_graphql import (
    commit_staged_changes_skip_deploy,
    read_service_source_binding,
    stage_github_source_disconnect,
)
from aethos_core.providers.railway.mutations import resolve_railway_mutation_credentials
from aethos_core.security.secret_redaction import redact_text


@dataclass(frozen=True)
class DisconnectGithubSourceResult:
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


def disconnect_github_source(
    *,
    environment_name: str,
    environment_id: str,
    service_id: str,
    repository: str,
    branch: str,
    idempotency_key: str,
) -> DisconnectGithubSourceResult:
    """
    Governed live disconnect_repo_source rollback mutation.

    Requires live_disconnect_github_source_authorization() from the live rollback executor.
    """
    _ = idempotency_key
    try:
        require_live_disconnect_github_source_authorization()
    except (LiveMutationNotAuthorizedError, LiveMutationKillSwitchActiveError, LiveMutationModeError) as exc:
        return DisconnectGithubSourceResult(ok=False, detail="", errors=[str(exc)])

    env_norm = (environment_name or "").strip().lower()
    if env_norm not in STAGING_ONLY_ENVIRONMENTS:
        return DisconnectGithubSourceResult(
            ok=False,
            detail="",
            errors=[
                "FIX 111 GitHub source disconnect is limited to staging environments "
                f"({', '.join(sorted(STAGING_ONLY_ENVIRONMENTS))})."
            ],
        )

    repo = (repository or "").strip()
    branch_name = (branch or "main").strip()
    if not service_id:
        return DisconnectGithubSourceResult(ok=False, detail="", errors=["service_id is required"])
    if not environment_id:
        return DisconnectGithubSourceResult(ok=False, detail="", errors=["environment_id is required"])

    token, source, cred_error = resolve_railway_mutation_credentials()
    if not token:
        return DisconnectGithubSourceResult(
            ok=False,
            detail="",
            errors=[redact_text(cred_error or f"Railway credentials unavailable (source={source}).")],
        )

    binding_read = read_service_source_binding(
        token,
        environment_id=environment_id,
        service_id=service_id,
    )
    if not binding_read.get("ok"):
        return DisconnectGithubSourceResult(
            ok=False,
            service_id=service_id,
            environment_id=environment_id,
            repository=repo,
            branch=branch_name,
            detail="",
            errors=[redact_text(str(binding_read.get("detail") or "source binding read failed"))],
        )

    if not binding_read.get("bound"):
        return DisconnectGithubSourceResult(
            ok=True,
            mutation_performed=False,
            idempotent_replay=True,
            service_id=service_id,
            environment_id=environment_id,
            repository=repo,
            branch=branch_name,
            detail="GitHub source already disconnected; no mutation performed.",
        )

    stage_result: dict[str, Any] = stage_github_source_disconnect(
        token,
        environment_id=environment_id,
        service_id=service_id,
    )
    if not stage_result.get("ok"):
        return DisconnectGithubSourceResult(
            ok=False,
            service_id=service_id,
            environment_id=environment_id,
            repository=repo,
            branch=branch_name,
            detail="",
            errors=[redact_text(str(stage_result.get("detail") or "stage disconnect failed"))],
        )

    commit_result = commit_staged_changes_skip_deploy(
        token,
        environment_id=environment_id,
        commit_message="AethOS governed GitHub source disconnect (FIX 111 rollback)",
    )
    if not commit_result.get("ok"):
        return DisconnectGithubSourceResult(
            ok=False,
            service_id=service_id,
            environment_id=environment_id,
            repository=repo,
            branch=branch_name,
            detail="",
            errors=[redact_text(str(commit_result.get("detail") or "commit failed"))],
        )

    verify = read_service_source_binding(
        token,
        environment_id=environment_id,
        service_id=service_id,
    )
    if verify.get("ok") and verify.get("bound"):
        return DisconnectGithubSourceResult(
            ok=False,
            service_id=service_id,
            environment_id=environment_id,
            repository=repo,
            branch=branch_name,
            detail="",
            errors=["post-disconnect verification: source still bound"],
        )

    return DisconnectGithubSourceResult(
        ok=True,
        mutation_performed=True,
        service_id=service_id,
        environment_id=environment_id,
        repository=repo,
        branch=branch_name,
        provider_request_id=f"railway:disconnect_source:{service_id}",
        detail="GitHub source disconnected via environmentStageChanges + commit (skipDeploys=true).",
    )
