# SPDX-License-Identifier: Apache-2.0
"""
FIX 114 — Read-only runtime verification adapter (verify_runtime phase).

Never calls deploy/restart mutations or re-triggers serviceInstanceRedeploy.
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
    require_runtime_verification_authorization,
)
from aethos_core.providers.railway.greenfield_adapters.runtime_verification_graphql import (
    read_deployment_runtime_status,
)
from aethos_core.providers.railway.mutations import resolve_railway_mutation_credentials
from aethos_core.security.secret_redaction import redact_text


@dataclass(frozen=True)
class VerifyRuntimeReadonlyResult:
    ok: bool
    verified: bool = False
    idempotent_replay: bool = False
    deployment_id: str = ""
    deployment_state: str = ""
    service_id: str = ""
    detail: str = ""
    errors: list[str] = field(default_factory=list)


def verify_runtime_readonly(
    *,
    environment_name: str,
    service_id: str,
    deployment_id: str,
    prior_verification: dict[str, Any] | None = None,
) -> VerifyRuntimeReadonlyResult:
    """Governed read-only verify_runtime check for a deployment on journal."""
    try:
        require_runtime_verification_authorization()
    except (LiveMutationNotAuthorizedError, LiveMutationKillSwitchActiveError, LiveMutationModeError) as exc:
        return VerifyRuntimeReadonlyResult(ok=False, detail="", errors=[str(exc)])

    env_norm = (environment_name or "").strip().lower()
    if env_norm not in STAGING_ONLY_ENVIRONMENTS:
        return VerifyRuntimeReadonlyResult(
            ok=False,
            detail="",
            errors=[
                "FIX 114 runtime verification is limited to staging environments "
                f"({', '.join(sorted(STAGING_ONLY_ENVIRONMENTS))})."
            ],
        )

    if not service_id or not deployment_id:
        return VerifyRuntimeReadonlyResult(
            ok=False,
            detail="",
            errors=["service_id and deployment_id are required for runtime verification"],
        )

    prior = prior_verification or {}
    if prior.get("verified") and str(prior.get("deployment_id") or "") == deployment_id:
        return VerifyRuntimeReadonlyResult(
            ok=True,
            verified=True,
            idempotent_replay=True,
            deployment_id=deployment_id,
            deployment_state=str(prior.get("deployment_state") or ""),
            service_id=service_id,
            detail="Runtime verification already recorded for this deployment; idempotent replay.",
        )

    token, source, cred_error = resolve_railway_mutation_credentials()
    if not token:
        return VerifyRuntimeReadonlyResult(
            ok=False,
            detail="",
            errors=[redact_text(cred_error or f"Railway credentials unavailable (source={source}).")],
        )

    read_result = read_deployment_runtime_status(
        token,
        service_id=service_id,
        deployment_id=deployment_id,
    )
    if not read_result.get("ok"):
        return VerifyRuntimeReadonlyResult(
            ok=False,
            service_id=service_id,
            deployment_id=deployment_id,
            detail="",
            errors=[redact_text(str(read_result.get("detail") or "deployment read failed"))],
        )

    observed_id = str(read_result.get("deployment_id") or deployment_id)
    state = str(read_result.get("deployment_state") or "")
    healthy = bool(read_result.get("deployment_healthy"))
    verified = healthy and observed_id == deployment_id

    detail = (
        f"runtime verification: deployment `{observed_id}` state=`{state}` "
        f"(healthy={str(healthy).lower()}); read-only, no redeploy."
    )
    if not verified:
        detail = (
            f"runtime verification failed for deployment `{observed_id}` state=`{state}` "
            "(read-only check only)."
        )

    return VerifyRuntimeReadonlyResult(
        ok=True,
        verified=verified,
        deployment_id=observed_id,
        deployment_state=state,
        service_id=service_id,
        detail=detail,
        errors=[] if verified else ["deployment_not_healthy"],
    )
