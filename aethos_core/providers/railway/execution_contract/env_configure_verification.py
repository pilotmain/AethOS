# SPDX-License-Identifier: Apache-2.0
"""FIX 112B — Read-only verification of Railway env var names (never values)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from aethos_core.providers.railway.execution_contract.env_configure_contract_models import (
    ENV_CONFIGURE_GROUP_MINIMUM_SECRETS,
    required_env_names_for_plan,
    resolve_env_configure_groups,
)
from aethos_core.providers.railway.greenfield_adapters.env_configure_graphql import (
    read_service_env_var_names,
)
from aethos_core.providers.railway.mutations import resolve_railway_mutation_credentials
from aethos_core.security.secret_redaction import redact_text


@dataclass(frozen=True)
class EnvConfigureVerification:
    ok: bool
    verified: bool
    readonly: bool = True
    minimum_secret_names_required: tuple[str, ...] = ()
    names_observed: tuple[str, ...] = ()
    missing_names: tuple[str, ...] = ()
    unexpected_extra_names: tuple[str, ...] = ()
    minimum_secrets_present: bool = False
    detail: str = ""
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "verified": self.verified,
            "readonly": self.readonly,
            "minimum_secret_names_required": list(self.minimum_secret_names_required),
            "names_observed": list(self.names_observed),
            "missing_names": list(self.missing_names),
            "unexpected_extra_names": list(self.unexpected_extra_names),
            "minimum_secrets_present": self.minimum_secrets_present,
            "detail": self.detail,
            "errors": list(self.errors),
        }


def _minimum_secret_names(*, plan: dict[str, Any] | None = None) -> tuple[str, ...]:
    names = required_env_names_for_plan(plan)
    if names:
        return names
    for group_id, group_names in resolve_env_configure_groups(plan):
        if group_id == ENV_CONFIGURE_GROUP_MINIMUM_SECRETS:
            return tuple(str(n).upper() for n in group_names)
    return ()


def verify_env_configure_readonly(
    *,
    environment_id: str,
    service_id: str,
    journal_env_names: list[str] | None = None,
    plan: dict[str, Any] | None = None,
) -> EnvConfigureVerification:
    """
    Read-only: confirm minimum secret env var names exist on the service.

    Never returns or logs secret values.
    """
    required = _minimum_secret_names(plan=plan)
    if not environment_id or not service_id:
        return EnvConfigureVerification(
            ok=False,
            verified=False,
            minimum_secret_names_required=required,
            detail="environment_id and service_id required for readonly env verification",
            errors=["missing_railway_target_ids"],
        )

    token, source, cred_error = resolve_railway_mutation_credentials()
    if not token:
        return EnvConfigureVerification(
            ok=False,
            verified=False,
            minimum_secret_names_required=required,
            detail=redact_text(cred_error or f"credentials unavailable (source={source})"),
            errors=["railway_credentials_unavailable"],
        )

    read_result = read_service_env_var_names(
        token,
        environment_id=environment_id,
        service_id=service_id,
    )
    if not read_result.get("ok"):
        return EnvConfigureVerification(
            ok=False,
            verified=False,
            minimum_secret_names_required=required,
            detail=redact_text(str(read_result.get("detail") or "env name read failed")),
            errors=["environment_config_read_failed"],
        )

    observed = {str(n).upper() for n in read_result.get("names") or []}
    if journal_env_names:
        observed |= {str(n).upper() for n in journal_env_names if str(n).strip()}

    missing = tuple(name for name in required if name not in observed)
    minimum_present = not missing and bool(required)
    verified = minimum_present

    return EnvConfigureVerification(
        ok=True,
        verified=verified,
        minimum_secret_names_required=required,
        names_observed=tuple(sorted(observed)),
        missing_names=missing,
        minimum_secrets_present=minimum_present,
        detail=(
            "minimum secret env names verified on service (read-only, values not read)"
            if verified
            else f"missing env names on service: {', '.join(missing)}"
        ),
        errors=[] if verified else ["minimum_secrets_missing_on_service"],
    )
