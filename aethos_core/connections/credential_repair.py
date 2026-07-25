# SPDX-License-Identifier: Apache-2.0
"""Repair metadata-only credentials and reconnect flows."""

from __future__ import annotations

from typing import Any

from aethos_core.connections.credential_audit import append_credential_audit_event
from aethos_core.connections.credential_state import resolve_credential_state
from aethos_core.connections.validation_status import RECONNECT_REQUIRED, VALIDATED
from aethos_core.security.credential_vault import get_credential_vault


def repair_metadata_only_credentials() -> list[dict[str, Any]]:
    """Scan vault; mark metadata-only rows reconnect_required (no silent delete)."""
    vault = get_credential_vault()
    repaired: list[dict[str, Any]] = []
    for rec in vault.list_credentials():
        state = resolve_credential_state(rec.credential_id)
        if state.get("metadata_found") and not state.get("decryptable"):
            vault.mark_validation_result(
                rec.credential_id,
                status=RECONNECT_REQUIRED,
                ok=False,
                diagnostics={
                    "failure_class": state.get("failure_class") or "encrypted_secret_missing",
                    "auth_source": "metadata_only",
                    "repair_action": "reconnect_required",
                },
            )
            append_credential_audit_event(
                event="credential_reconnect_required",
                provider=rec.provider,
                credential_id=rec.credential_id,
                detail="encrypted secret missing",
                validation_status=RECONNECT_REQUIRED,
            )
            repaired.append(
                {
                    "provider": rec.provider,
                    "credential_id": rec.credential_id,
                    "credential_state": RECONNECT_REQUIRED,
                    "failure_class": state.get("failure_class"),
                }
            )
    return repaired


def forget_stale_provider_credentials(provider: str) -> list[str]:
    """Revoke all credentials for provider (repair reconnect prep)."""
    vault = get_credential_vault()
    revoked: list[str] = []
    for rec in vault.list_credentials(provider=provider):
        vault.revoke(rec.credential_id)
        append_credential_audit_event(
            event="credential_forgotten",
            provider=provider,
            credential_id=rec.credential_id,
            detail="repair reconnect",
        )
        revoked.append(rec.credential_id)
    return revoked


def repair_provider_credential(
    *,
    provider: str,
    token: str,
    label: str = "",
    scope: list[str] | None = None,
    write_allowed: bool = False,
) -> dict[str, Any]:
    """Forget stale metadata, store fresh token, validate persistence + provider."""
    from aethos_core.connections.credential_hydration import reload_credential_runtime
    from aethos_core.connections.credential_validation import validate_provider_credential

    forget_stale_provider_credentials(provider)
    vault = get_credential_vault()
    record = vault.store_api_token(
        provider=provider,
        label=label or f"{provider} API token",
        token=token,
        scope=scope,
        write_allowed=write_allowed,
    )
    validation = validate_provider_credential(provider=provider, credential_id=record.credential_id)
    reload_credential_runtime(validate=True)
    state = resolve_credential_state(record.credential_id)
    return {
        "credential_id": record.credential_id,
        "provider": provider,
        "validation": validation,
        "credential_state": state.get("credential_state"),
        "decryptable": state.get("decryptable"),
        "auth_source": state.get("auth_source"),
        "runtime_usable": state.get("runtime_usable") and validation.get("status") == VALIDATED,
    }
