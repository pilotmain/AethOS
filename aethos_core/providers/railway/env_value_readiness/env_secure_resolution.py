# SPDX-License-Identifier: Apache-2.0
"""Resolve env values from secure store — credential vault, deployment store, solo."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from aethos_core.providers.railway.env_value_readiness.env_value_inventory import (
    _local_trusted_secret_value,
)
from aethos_core.providers.railway.env_value_readiness.env_value_readiness import (
    _PROVIDER_ENV_MAP,
    build_target_key,
)

_ALLOWED_SOURCES = frozenset({"credential_center", "secure_store_reference"})
_FORBIDDEN_SOURCES = frozenset({"local_env_dev_only", "chat", "user_message", "session"})


@dataclass(frozen=True)
class SecureEnvResolution:
    name: str
    ok: bool
    value: str = ""
    source: str = ""
    blocked_reason: str = ""
    errors: list[str] = field(default_factory=list)


def _resolve_solo_local_secret(env_name: str) -> SecureEnvResolution | None:
    from aethos_core.solo_execution.solo_execution_mode import is_solo_execution_mode_enabled

    if not is_solo_execution_mode_enabled():
        return None
    value = _local_trusted_secret_value(env_name)
    if not value:
        return None
    return SecureEnvResolution(
        name=env_name.strip().upper(),
        ok=True,
        value=value,
        source="credential_center",
    )


def _resolve_from_credential_vault(env_name: str) -> SecureEnvResolution:
    upper = env_name.strip().upper()
    provider = _PROVIDER_ENV_MAP.get(upper)
    if provider:
        try:
            from aethos_core.credentials import get_provider_api_token

            token = get_provider_api_token(provider, require_validated=False)
            if token and str(token).strip():
                return SecureEnvResolution(
                    name=upper,
                    ok=True,
                    value=str(token).strip(),
                    source="credential_center",
                )
        except Exception as exc:
            return SecureEnvResolution(
                name=upper,
                ok=False,
                blocked_reason="credential_center_unavailable",
                errors=[str(exc)],
            )

    try:
        from aethos_core.security.credential_vault import get_credential_vault

        vault = get_credential_vault()
        for rec in vault.list_credentials():
            label = str(rec.label or "").upper()
            if upper in label or label == upper:
                secret = vault.retrieve_secret(rec.credential_id) or {}
                token = str(secret.get("token") or secret.get("value") or "").strip()
                if token:
                    return SecureEnvResolution(
                        name=upper,
                        ok=True,
                        value=token,
                        source="credential_center",
                    )
    except Exception as exc:
        return SecureEnvResolution(
            name=upper,
            ok=False,
            blocked_reason="credential_vault_error",
            errors=[str(exc)],
        )

    return SecureEnvResolution(
        name=upper,
        ok=False,
        blocked_reason="secure_store_missing",
        errors=[f"No credential vault entry for `{upper}`."],
    )


def resolve_env_var_from_secure_store(
    name: str,
    *,
    plan: dict[str, Any],
) -> SecureEnvResolution:
    """
    Resolve one env var for live Railway configure_env.

    Order: deployment encrypted store → provider Connections → solo local (dev).
  Values never logged; names-only in audit elsewhere.
    """
    env_name = (name or "").strip().upper()
    if not env_name:
        return SecureEnvResolution(name="", ok=False, blocked_reason="empty_name", errors=["empty env name"])

    plan = dict(plan or {})

    if env_name == "NEXT_PUBLIC_API_BASE" and str(plan.get("deploy_component") or "") == "ui":
        from aethos_core.providers.railway.greenfield_deployment.greenfield_deploy_component import (
            resolve_ui_public_api_base,
        )

        ui_base = resolve_ui_public_api_base(plan=plan)
        if ui_base:
            return SecureEnvResolution(
                name=env_name,
                ok=True,
                value=ui_base,
                source="credential_center",
            )

    target_key = build_target_key_for_plan(plan)

    from aethos_core.providers.railway.env_value_readiness.deployment_env_store import (
        resolve_deployment_env_value,
    )

    stored = resolve_deployment_env_value(target_key=target_key, name=env_name)
    if stored:
        return SecureEnvResolution(
            name=env_name,
            ok=True,
            value=stored,
            source="secure_store_reference",
        )

    vault_resolved = _resolve_from_credential_vault(env_name)
    if vault_resolved.ok:
        return vault_resolved

    solo_value = _resolve_solo_local_secret(env_name)
    if solo_value is not None:
        return solo_value

    from aethos_core.providers.railway.env_value_readiness.env_value_inventory import probe_env_var_presence

    presence = probe_env_var_presence(env_name, plan=plan)
    source = str(presence.get("source") or "")
    if source in _FORBIDDEN_SOURCES:
        return SecureEnvResolution(
            name=env_name,
            ok=False,
            blocked_reason="forbidden_source",
            errors=[f"`{env_name}` is not available via secure store (source={source})."],
        )

    detail = (
        f"`{env_name}` is not present in secure store for this deployment target."
        if not presence.get("present")
        else f"`{env_name}` could not be resolved from secure store."
    )
    return SecureEnvResolution(
        name=env_name,
        ok=False,
        blocked_reason="not_present_in_secure_store",
        errors=[detail],
    )


def build_target_key_for_plan(plan: dict[str, Any]) -> str:
    return build_target_key(
        repo=str(plan.get("repo") or ""),
        project=str(plan.get("project") or ""),
        environment=str(plan.get("environment") or ""),
        service_name=str(plan.get("service_name") or ""),
    )
