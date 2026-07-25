# SPDX-License-Identifier: Apache-2.0
"""
FIX 112 — Governed configure_env (secure store only, staging, skipDeploys).

Never logs or returns secret values in result detail.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from aethos_core.providers.railway.execution_contract.env_configure_contract_models import (
    ENV_CONFIGURE_GROUP_UI_RUNTIME,
)
from aethos_core.providers.railway.env_value_readiness.env_secure_resolution import (
    resolve_env_var_from_secure_store,
)
from aethos_core.providers.railway.greenfield_adapters.env_configure_graphql import (
    commit_staged_env_changes_skip_deploy,
    read_service_env_var_names,
    stage_service_env_variables,
)
from aethos_core.providers.railway.greenfield_adapters.greenfield_mutation_scope import (
    STAGING_ONLY_ENVIRONMENTS,
)
from aethos_core.providers.railway.greenfield_adapters.mutation_live_gate import (
    LiveMutationKillSwitchActiveError,
    LiveMutationModeError,
    LiveMutationNotAuthorizedError,
    require_live_configure_env_authorization,
)
from aethos_core.providers.railway.mutations import resolve_railway_mutation_credentials
from aethos_core.security.secret_redaction import redact_text


@dataclass(frozen=True)
class ConfigureEnvGroupResult:
    ok: bool
    group_id: str = ""
    mutation_performed: bool = False
    idempotent_replay: bool = False
    env_names_written: tuple[str, ...] = ()
    version_fingerprint: str = ""
    service_id: str = ""
    environment_id: str = ""
    detail: str = ""
    errors: list[str] = field(default_factory=list)


def configure_env_group(
    *,
    environment_name: str,
    environment_id: str,
    service_id: str,
    group_id: str,
    env_names: tuple[str, ...],
    plan: dict[str, Any],
    existing_names_on_service: set[str] | None = None,
    version_fingerprint: str = "",
    journal_group_state: dict[str, Any] | None = None,
) -> ConfigureEnvGroupResult:
    """
    Write one env var group to Railway from secure store only.

    Idempotent when journal fingerprint matches and all keys already on service.
    """
    try:
        require_live_configure_env_authorization()
    except (LiveMutationNotAuthorizedError, LiveMutationKillSwitchActiveError, LiveMutationModeError) as exc:
        return ConfigureEnvGroupResult(ok=False, group_id=group_id, errors=[str(exc)])

    env_norm = (environment_name or "").strip().lower()
    if env_norm not in STAGING_ONLY_ENVIRONMENTS:
        return ConfigureEnvGroupResult(
            ok=False,
            group_id=group_id,
            errors=[
                "FIX 112 env writes are limited to staging environments "
                f"({', '.join(sorted(STAGING_ONLY_ENVIRONMENTS))})."
            ],
        )

    if not service_id or not environment_id:
        return ConfigureEnvGroupResult(
            ok=False,
            group_id=group_id,
            errors=["service_id and environment_id are required"],
        )

    names = tuple(n.strip().upper() for n in env_names if str(n).strip())
    if not names:
        return ConfigureEnvGroupResult(
            ok=False,
            group_id=group_id,
            errors=["env group has no names"],
        )

    prior = journal_group_state or {}
    if (
        prior.get("version_fingerprint") == version_fingerprint
        and prior.get("mutation_performed")
        and set(prior.get("env_names") or []) >= set(names)
    ):
        existing = existing_names_on_service or set()
        if existing and all(n in existing for n in names):
            return ConfigureEnvGroupResult(
                ok=True,
                group_id=group_id,
                mutation_performed=False,
                idempotent_replay=True,
                env_names_written=names,
                version_fingerprint=version_fingerprint,
                service_id=service_id,
                environment_id=environment_id,
                detail=f"group `{group_id}` already configured; idempotent replay.",
            )

    variables: dict[str, str] = {}
    for env_name in names:
        resolved = resolve_env_var_from_secure_store(env_name, plan=plan)
        if not resolved.ok:
            return ConfigureEnvGroupResult(
                ok=False,
                group_id=group_id,
                env_names_written=names,
                version_fingerprint=version_fingerprint,
                errors=[f"{env_name}: {resolved.blocked_reason}; " + "; ".join(resolved.errors)],
            )
        variables[env_name] = resolved.value

    token, source, cred_error = resolve_railway_mutation_credentials()
    if not token:
        return ConfigureEnvGroupResult(
            ok=False,
            group_id=group_id,
            errors=[redact_text(cred_error or f"Railway credentials unavailable (source={source}).")],
        )

    read_names = read_service_env_var_names(
        token,
        environment_id=environment_id,
        service_id=service_id,
    )
    if read_names.get("ok") and group_id != ENV_CONFIGURE_GROUP_UI_RUNTIME:
        present = {str(n).upper() for n in read_names.get("names") or []}
        if present and all(n in present for n in names):
            return ConfigureEnvGroupResult(
                ok=True,
                group_id=group_id,
                mutation_performed=False,
                idempotent_replay=True,
                env_names_written=names,
                version_fingerprint=version_fingerprint,
                service_id=service_id,
                environment_id=environment_id,
                detail=f"group `{group_id}` keys already present on service; idempotent replay.",
            )

    stage_result = stage_service_env_variables(
        token,
        environment_id=environment_id,
        service_id=service_id,
        variables=variables,
    )
    if not stage_result.get("ok"):
        return ConfigureEnvGroupResult(
            ok=False,
            group_id=group_id,
            env_names_written=names,
            errors=[redact_text(str(stage_result.get("detail") or "stage failed"))],
        )

    commit_result = commit_staged_env_changes_skip_deploy(
        token,
        environment_id=environment_id,
        commit_message=f"AethOS governed env configure group={group_id} (FIX 112)",
    )
    if not commit_result.get("ok"):
        return ConfigureEnvGroupResult(
            ok=False,
            group_id=group_id,
            env_names_written=names,
            errors=[redact_text(str(commit_result.get("detail") or "commit failed"))],
        )

    verify = {"ok": False, "names": []}
    for attempt in range(4):
        verify = read_service_env_var_names(
            token,
            environment_id=environment_id,
            service_id=service_id,
        )
        if verify.get("ok"):
            present = {str(n).upper() for n in verify.get("names") or []}
            missing = [n for n in names if n not in present]
            if not missing:
                break
        if attempt < 3:
            import time

            time.sleep(1.0)
    if verify.get("ok"):
        present = {str(n).upper() for n in verify.get("names") or []}
        missing = [n for n in names if n not in present]
        if missing:
            return ConfigureEnvGroupResult(
                ok=False,
                group_id=group_id,
                env_names_written=names,
                errors=[f"post-write verification missing keys: {', '.join(missing)}"],
            )

    return ConfigureEnvGroupResult(
        ok=True,
        group_id=group_id,
        mutation_performed=True,
        env_names_written=names,
        version_fingerprint=version_fingerprint,
        service_id=service_id,
        environment_id=environment_id,
        detail=(
            f"group `{group_id}` configured ({len(names)} vars) via stage+commit; "
            "skipDeploys enforced; no values logged."
        ),
    )
