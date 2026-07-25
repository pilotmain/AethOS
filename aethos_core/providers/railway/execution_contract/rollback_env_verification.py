# SPDX-License-Identifier: Apache-2.0
"""FIX 115 — Read-only rollback env verification (names only)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from aethos_core.providers.railway.execution_contract.env_configure_contract_models import (
    ENV_CONFIGURE_GROUPS,
)
from aethos_core.providers.railway.greenfield_adapters.env_configure_graphql import (
    read_service_env_var_names,
)
from aethos_core.providers.railway.mutations import resolve_railway_mutation_credentials
from aethos_core.security.secret_redaction import redact_text


@dataclass(frozen=True)
class RollbackEnvVerification:
    ok: bool
    verified: bool = False
    readonly: bool = True
    names_expected_absent: tuple[str, ...] = ()
    names_still_present: tuple[str, ...] = ()
    detail: str = ""
    errors: list[str] = field(default_factory=list)


def _minimum_secret_names() -> tuple[str, ...]:
    names: list[str] = []
    for _gid, group_names in ENV_CONFIGURE_GROUPS:
        names.extend(str(n).upper() for n in group_names)
    return tuple(sorted(set(names)))


def verify_rollback_env_readonly(
    *,
    environment_id: str,
    service_id: str,
) -> RollbackEnvVerification:
    required = _minimum_secret_names()
    if not environment_id or not service_id:
        return RollbackEnvVerification(
            ok=False,
            verified=False,
            names_expected_absent=required,
            detail="environment_id and service_id required",
            errors=["missing_railway_target_ids"],
        )

    token, _source, cred_error = resolve_railway_mutation_credentials()
    if not token:
        return RollbackEnvVerification(
            ok=False,
            verified=False,
            names_expected_absent=required,
            detail="",
            errors=[redact_text(cred_error or "credentials unavailable")],
        )

    read_result = read_service_env_var_names(
        token,
        environment_id=environment_id,
        service_id=service_id,
    )
    if not read_result.get("ok"):
        return RollbackEnvVerification(
            ok=False,
            verified=False,
            names_expected_absent=required,
            detail="",
            errors=[redact_text(str(read_result.get("detail") or "read failed"))],
        )

    observed = {str(n).upper() for n in read_result.get("names") or []}
    still_present = tuple(sorted(n for n in required if n in observed))
    verified = not still_present
    detail = (
        "rollback env verification passed (minimum secrets absent)"
        if verified
        else f"rollback env verification failed; names still present: {', '.join(still_present)}"
    )
    return RollbackEnvVerification(
        ok=True,
        verified=verified,
        names_expected_absent=required,
        names_still_present=still_present,
        detail=detail,
        errors=[] if verified else ["env_names_still_present"],
    )
