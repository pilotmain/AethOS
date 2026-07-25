# SPDX-License-Identifier: Apache-2.0
"""
FIX 108 — First governed Railway mutation: create empty service only.

This module is the sole live-mutation entry for greenfield service creation.
Dry-run and simulation paths must never import or call these functions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from aethos_core.providers.railway.greenfield_adapters.service_create_graphql import (
    invoke_service_create,
)
from aethos_core.providers.railway.greenfield_adapters.target_resolution import (
    RailwayTargetResolution,
    find_service_in_project,
    resolve_railway_create_targets,
    service_name_exists_in_project,
)
from aethos_core.providers.railway.greenfield_adapters.mutation_live_gate import (
    LiveMutationKillSwitchActiveError,
    LiveMutationModeError,
    LiveMutationNotAuthorizedError,
    require_live_create_service_authorization,
)
from aethos_core.providers.railway.mutations import resolve_railway_mutation_credentials
from aethos_core.security.secret_redaction import redact_text

from aethos_core.providers.railway.greenfield_adapters.greenfield_mutation_scope import (
    STAGING_ONLY_ENVIRONMENTS,
)

# Back-compat alias (FIX 108).
FIX108_REAL_MUTATION_ENVIRONMENTS = STAGING_ONLY_ENVIRONMENTS


@dataclass(frozen=True)
class CreateRailwayServiceResult:
    ok: bool
    mutation_performed: bool = False
    idempotent_replay: bool = False
    service_id: str = ""
    service_name: str = ""
    project_id: str = ""
    environment_id: str = ""
    provider_request_id: str = ""
    detail: str = ""
    errors: list[str] = field(default_factory=list)


def create_railway_service(
    *,
    project_name: str,
    environment_name: str,
    service_name: str,
    idempotency_key: str,
    existing_service_id: str = "",
) -> CreateRailwayServiceResult:
    """
    Governed live create_service mutation.

    Preconditions are enforced by the real-mutation executor (enablement, staging-only,
    rollback journal, lock). This function performs credential resolution, target resolution,
    optional idempotent skip, and the Railway serviceCreate call.
    """
    try:
        require_live_create_service_authorization()
    except (LiveMutationNotAuthorizedError, LiveMutationKillSwitchActiveError, LiveMutationModeError) as exc:
        return CreateRailwayServiceResult(ok=False, detail="", errors=[str(exc)])

    _ = idempotency_key
    env_norm = (environment_name or "").strip().lower()
    if env_norm not in FIX108_REAL_MUTATION_ENVIRONMENTS:
        return CreateRailwayServiceResult(
            ok=False,
            mutation_performed=False,
            detail="",
            errors=[
                "FIX 108 real mutations are limited to staging environments "
                f"({', '.join(sorted(STAGING_ONLY_ENVIRONMENTS))})."
            ],
        )

    if existing_service_id:
        return CreateRailwayServiceResult(
            ok=True,
            mutation_performed=False,
            idempotent_replay=True,
            service_id=existing_service_id,
            service_name=service_name,
            detail="create_service skipped — idempotent replay (service already recorded on journal).",
        )

    token, source, cred_error = resolve_railway_mutation_credentials()
    if not token:
        return CreateRailwayServiceResult(
            ok=False,
            detail="",
            errors=[redact_text(cred_error or f"Railway credentials unavailable (source={source}).")],
        )

    targets: RailwayTargetResolution = resolve_railway_create_targets(
        project_name=project_name,
        environment_name=environment_name,
    )
    if not targets.ok:
        return CreateRailwayServiceResult(ok=False, detail="", errors=list(targets.errors))

    if service_name_exists_in_project(project_id=targets.project_id, service_name=service_name):
        existing = find_service_in_project(
            project_id=targets.project_id,
            service_name=service_name,
            environment_name=environment_name,
        ) or find_service_in_project(project_id=targets.project_id, service_name=service_name)
        return CreateRailwayServiceResult(
            ok=True,
            mutation_performed=False,
            idempotent_replay=True,
            service_id=str((existing or {}).get("service_id") or ""),
            project_id=str((existing or {}).get("project_id") or targets.project_id),
            environment_id=str((existing or {}).get("environment_id") or targets.environment_id),
            service_name=str((existing or {}).get("service_name") or service_name),
            detail=(
                f"Service `{service_name}` already exists in project `{targets.project_name}`; "
                "reusing existing service (no serviceCreate mutation performed)."
            ),
        )

    api_result: dict[str, Any] = invoke_service_create(
        token,
        project_id=targets.project_id,
        service_name=service_name,
        environment_id=targets.environment_id,
    )
    if not api_result.get("ok"):
        return CreateRailwayServiceResult(
            ok=False,
            mutation_performed=False,
            project_id=targets.project_id,
            environment_id=targets.environment_id,
            detail="",
            errors=[redact_text(str(api_result.get("detail") or "serviceCreate failed"))],
        )

    service_id = str(api_result.get("service_id") or "")
    return CreateRailwayServiceResult(
        ok=True,
        mutation_performed=True,
        service_id=service_id,
        service_name=str(api_result.get("service_name") or service_name),
        project_id=targets.project_id,
        environment_id=targets.environment_id,
        provider_request_id=f"railway:serviceCreate:{service_id}",
        detail=str(api_result.get("detail") or "serviceCreate succeeded"),
    )
