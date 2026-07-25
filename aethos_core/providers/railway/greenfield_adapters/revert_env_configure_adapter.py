# SPDX-License-Identifier: Apache-2.0
"""FIX 115 — Governed revert_env_writes (unset FIX 112 minimum secrets only)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from aethos_core.providers.railway.execution_contract.env_configure_contract_models import (
    ENV_CONFIGURE_GROUPS,
)
from aethos_core.providers.railway.greenfield_adapters.env_configure_graphql import (
    commit_staged_env_changes_skip_deploy,
    read_service_env_var_names,
    stage_service_env_unset,
)
from aethos_core.providers.railway.greenfield_adapters.greenfield_mutation_scope import (
    STAGING_ONLY_ENVIRONMENTS,
)
from aethos_core.providers.railway.greenfield_adapters.mutation_live_gate import (
    LiveMutationKillSwitchActiveError,
    LiveMutationModeError,
    LiveMutationNotAuthorizedError,
    require_live_revert_env_authorization,
)
from aethos_core.providers.railway.mutations import resolve_railway_mutation_credentials
from aethos_core.security.secret_redaction import redact_text


@dataclass(frozen=True)
class RevertEnvConfigureResult:
    ok: bool
    mutation_performed: bool = False
    idempotent_replay: bool = False
    env_names_reverted: tuple[str, ...] = ()
    service_id: str = ""
    environment_id: str = ""
    detail: str = ""
    errors: list[str] = field(default_factory=list)


def _allowed_revert_names() -> tuple[str, ...]:
    names: list[str] = []
    for _group_id, group_names in ENV_CONFIGURE_GROUPS:
        names.extend(str(n).upper() for n in group_names)
    return tuple(sorted(set(names)))


def revert_env_writes(
    *,
    environment_name: str,
    environment_id: str,
    service_id: str,
    journal_env_names: list[str] | None = None,
) -> RevertEnvConfigureResult:
    """Unset only env var names written by FIX 112 (never arbitrary deletion)."""
    try:
        require_live_revert_env_authorization()
    except (LiveMutationNotAuthorizedError, LiveMutationKillSwitchActiveError, LiveMutationModeError) as exc:
        return RevertEnvConfigureResult(ok=False, errors=[str(exc)])

    env_norm = (environment_name or "").strip().lower()
    if env_norm not in STAGING_ONLY_ENVIRONMENTS:
        return RevertEnvConfigureResult(
            ok=False,
            errors=[
                "FIX 115 env rollback is limited to staging environments "
                f"({', '.join(sorted(STAGING_ONLY_ENVIRONMENTS))})."
            ],
        )

    if not service_id or not environment_id:
        return RevertEnvConfigureResult(
            ok=False,
            errors=["service_id and environment_id are required"],
        )

    allowed = set(_allowed_revert_names())
    journal_names = {str(n).upper() for n in (journal_env_names or []) if str(n).strip()}
    target_names = sorted(allowed & journal_names) if journal_names else sorted(allowed)
    if not target_names:
        return RevertEnvConfigureResult(
            ok=False,
            errors=["no FIX 112 env names eligible for revert"],
        )

    token, _source, cred_error = resolve_railway_mutation_credentials()
    if not token:
        return RevertEnvConfigureResult(
            ok=False,
            errors=[redact_text(cred_error or "Railway credentials unavailable.")],
        )

    read_result = read_service_env_var_names(
        token,
        environment_id=environment_id,
        service_id=service_id,
    )
    if not read_result.get("ok"):
        return RevertEnvConfigureResult(
            ok=False,
            errors=[redact_text(str(read_result.get("detail") or "env name read failed"))],
        )

    observed = {str(n).upper() for n in read_result.get("names") or []}
    to_unset = [name for name in target_names if name in observed]
    if not to_unset:
        return RevertEnvConfigureResult(
            ok=True,
            mutation_performed=False,
            idempotent_replay=True,
            env_names_reverted=tuple(target_names),
            service_id=service_id,
            environment_id=environment_id,
            detail="FIX 112 env names already absent; idempotent replay.",
        )

    stage_result = stage_service_env_unset(
        token,
        environment_id=environment_id,
        service_id=service_id,
        env_names=to_unset,
    )
    if not stage_result.get("ok"):
        return RevertEnvConfigureResult(
            ok=False,
            errors=[redact_text(str(stage_result.get("detail") or "env unset stage failed"))],
        )

    commit_result = commit_staged_env_changes_skip_deploy(
        token,
        environment_id=environment_id,
        commit_message="AethOS governed revert_env_writes (FIX 115)",
    )
    if not commit_result.get("ok"):
        return RevertEnvConfigureResult(
            ok=False,
            errors=[redact_text(str(commit_result.get("detail") or "env unset commit failed"))],
        )

    return RevertEnvConfigureResult(
        ok=True,
        mutation_performed=True,
        env_names_reverted=tuple(to_unset),
        service_id=service_id,
        environment_id=environment_id,
        detail=(
            f"reverted env names (names only): {', '.join(to_unset)}; "
            "skipDeploys=true; no deploy trigger."
        ),
    )
