# SPDX-License-Identifier: Apache-2.0
"""Canonical credential lifecycle states."""

from __future__ import annotations

from typing import Any

from aethos_core.connections.validation_status import (
    CONFIGURED,
    EXPIRED,
    INSUFFICIENT_SCOPE,
    INVALID,
    MISSING,
    PERSISTENCE_FAILED,
    RECONNECT_REQUIRED,
    SECRET_MISSING,
    VALIDATED,
)


def resolve_credential_state(credential_id: str) -> dict[str, Any]:
    from aethos_core.security.credential_vault import get_credential_vault

    vault = get_credential_vault()
    rec = vault.get(credential_id)
    storage = vault.inspect_secret_storage(credential_id)
    has_metadata = bool(storage.get("has_metadata"))
    decryptable = bool(storage.get("decryptable"))
    has_secret = bool(storage.get("has_encrypted_secret"))
    failure_class = storage.get("failure_class")
    auth_source = storage.get("auth_source") or "none"

    base: dict[str, Any] = {
        "credential_id": credential_id,
        "provider": rec.provider if rec else None,
        "metadata_found": has_metadata,
        "encrypted_secret_found": has_secret,
        "decryptable": decryptable,
        "failure_class": failure_class,
        "auth_source": auth_source,
        "validation_status": rec.validation_status if rec else MISSING,
        "secret_file_path": storage.get("secret_file_path"),
        "vault_path": storage.get("vault_path"),
    }

    if not rec:
        return {**base, "credential_state": MISSING, "hydrated": False, "runtime_usable": False}
    if not decryptable:
        state = RECONNECT_REQUIRED
        if failure_class == "encrypted_secret_missing" or auth_source == "metadata_only":
            state = RECONNECT_REQUIRED
        elif rec.validation_status == PERSISTENCE_FAILED:
            state = PERSISTENCE_FAILED
        else:
            state = RECONNECT_REQUIRED
        return {
            **base,
            "credential_state": state,
            "hydrated": False,
            "runtime_usable": False,
        }
    if rec.validation_status == VALIDATED:
        return {
            **base,
            "credential_state": VALIDATED,
            "hydrated": True,
            "runtime_usable": True,
        }
    if rec.validation_status == PERSISTENCE_FAILED:
        return {**base, "credential_state": PERSISTENCE_FAILED, "hydrated": False, "runtime_usable": False}
    if rec.validation_status == EXPIRED:
        return {**base, "credential_state": EXPIRED, "hydrated": False, "runtime_usable": False}
    if rec.validation_status in (INVALID, INSUFFICIENT_SCOPE, SECRET_MISSING):
        return {
            **base,
            "credential_state": rec.validation_status,
            "hydrated": False,
            "runtime_usable": False,
        }
    return {
        **base,
        "credential_state": CONFIGURED,
        "hydrated": decryptable,
        "runtime_usable": False,
    }


def provider_credential_state(*, provider: str) -> dict[str, Any]:
    from aethos_core.credentials.provider_alias_resolution import list_credentials_for_canonical

    creds = list_credentials_for_canonical(provider)
    if not creds:
        return {
            "provider": provider,
            "credential_state": MISSING,
            "metadata_found": False,
            "encrypted_secret_found": False,
            "decryptable": False,
            "hydrated": False,
            "runtime_usable": False,
            "auth_source": "none",
        }
    latest = resolve_credential_state(creds[0].credential_id)
    latest["provider"] = provider
    return latest


def connection_api_token_status(*, provider: str) -> str:
    state = provider_credential_state(provider=provider)
    credential_state = str(state.get("credential_state") or MISSING)
    if credential_state == VALIDATED:
        return "validated"
    if credential_state == MISSING:
        return "missing"
    if credential_state in (RECONNECT_REQUIRED, SECRET_MISSING, PERSISTENCE_FAILED):
        return "reconnect_required"
    if credential_state == CONFIGURED:
        return "configured"
    return credential_state
