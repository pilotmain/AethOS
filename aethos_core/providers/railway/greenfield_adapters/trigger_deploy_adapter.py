# SPDX-License-Identifier: Apache-2.0
"""
FIX 113 — Governed deploy trigger (trigger_deploy phase only).

Invokes serviceInstanceRedeploy only. No runtime verification (FIX 114).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from aethos_core.providers.railway.greenfield_adapters.deploy_trigger_graphql import (
    trigger_service_instance_deploy,
)
from aethos_core.providers.railway.greenfield_adapters.greenfield_mutation_scope import (
    STAGING_ONLY_ENVIRONMENTS,
)
from aethos_core.providers.railway.greenfield_adapters.mutation_live_gate import (
    LiveMutationKillSwitchActiveError,
    LiveMutationModeError,
    LiveMutationNotAuthorizedError,
    require_live_trigger_deploy_authorization,
)
from aethos_core.providers.railway.mutations import resolve_railway_mutation_credentials
from aethos_core.security.secret_redaction import redact_text


@dataclass(frozen=True)
class TriggerDeployResult:
    ok: bool
    mutation_performed: bool = False
    idempotent_replay: bool = False
    service_id: str = ""
    environment_id: str = ""
    deployment_id: str = ""
    deployment_url: str = ""
    graphql_operation: str = ""
    provider_request_id: str = ""
    detail: str = ""
    errors: list[str] = field(default_factory=list)


def trigger_railway_deploy(
    *,
    environment_name: str,
    environment_id: str,
    service_id: str,
    idempotency_key: str,
    existing_deployment_id: str = "",
) -> TriggerDeployResult:
    """
    Governed live trigger_deploy mutation.

    Requires live_trigger_deploy_authorization() from the real-mutation executor.
    """
    _ = idempotency_key
    try:
        require_live_trigger_deploy_authorization()
    except (LiveMutationNotAuthorizedError, LiveMutationKillSwitchActiveError, LiveMutationModeError) as exc:
        return TriggerDeployResult(ok=False, detail="", errors=[str(exc)])

    env_norm = (environment_name or "").strip().lower()
    if env_norm not in STAGING_ONLY_ENVIRONMENTS:
        return TriggerDeployResult(
            ok=False,
            detail="",
            errors=[
                "FIX 113 deploy trigger is limited to staging environments "
                f"({', '.join(sorted(STAGING_ONLY_ENVIRONMENTS))})."
            ],
        )

    if not service_id or not environment_id:
        return TriggerDeployResult(
            ok=False,
            detail="",
            errors=["service_id and environment_id are required for deploy trigger"],
        )

    if existing_deployment_id:
        return TriggerDeployResult(
            ok=True,
            mutation_performed=False,
            idempotent_replay=True,
            service_id=service_id,
            environment_id=environment_id,
            deployment_id=existing_deployment_id,
            graphql_operation="serviceInstanceRedeploy",
            provider_request_id=existing_deployment_id,
            detail="Deploy already triggered for this execution; idempotent replay.",
        )

    token, source, cred_error = resolve_railway_mutation_credentials()
    if not token:
        return TriggerDeployResult(
            ok=False,
            detail="",
            errors=[redact_text(cred_error or f"Railway credentials unavailable (source={source}).")],
        )

    deploy_result = trigger_service_instance_deploy(
        token,
        environment_id=environment_id,
        service_id=service_id,
    )
    if not deploy_result.get("ok"):
        return TriggerDeployResult(
            ok=False,
            service_id=service_id,
            environment_id=environment_id,
            detail="",
            errors=[redact_text(str(deploy_result.get("detail") or "deploy trigger failed"))],
        )

    deployment_id = str(deploy_result.get("deployment_id") or "")
    return TriggerDeployResult(
        ok=True,
        mutation_performed=True,
        service_id=service_id,
        environment_id=environment_id,
        deployment_id=deployment_id,
        deployment_url=str(deploy_result.get("deployment_url") or ""),
        graphql_operation=str(deploy_result.get("graphql_operation") or "serviceInstanceRedeploy"),
        provider_request_id=deployment_id,
        detail=(
            "Deploy triggered via serviceInstanceRedeploy. "
            "Runtime verification is not performed in FIX 113."
        ),
    )
