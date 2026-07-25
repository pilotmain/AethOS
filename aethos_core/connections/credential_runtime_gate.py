# SPDX-License-Identifier: Apache-2.0
"""Runtime credential gating — only validated, decryptable secrets are usable."""

from __future__ import annotations

from typing import Any

from aethos_core.connections.credential_state import resolve_credential_state
from aethos_core.connections.validation_status import RECONNECT_REQUIRED, VALIDATED


class CredentialGateError(Exception):
    def __init__(
        self,
        message: str,
        *,
        provider: str,
        credential_state: str,
        failure_class: str | None = None,
        auth_source: str | None = None,
    ) -> None:
        super().__init__(message)
        self.provider = provider
        self.credential_state = credential_state
        self.failure_class = failure_class
        self.auth_source = auth_source


def credential_gate_message(*, provider: str, state_info: dict[str, Any]) -> str:
    label = provider.replace("_", " ").title()
    state = state_info.get("credential_state")
    auth_source = state_info.get("auth_source")
    if auth_source == "metadata_only" or state == RECONNECT_REQUIRED:
        return f"Credential reconnect required for {label}. Encrypted secret is missing."
    if state == "persistence_failed":
        return f"Credential persistence failed for {label}. Reconnect to store a durable secret."
    if state == VALIDATED:
        return ""
    return f"Credential repair required for {label} before this operation."


def check_credential_gate(
    credential_id: str,
    *,
    provider: str | None = None,
    require_validated: bool = True,
) -> dict[str, Any]:
    state_info = resolve_credential_state(credential_id)
    if provider and state_info.get("provider"):
        from aethos_core.credentials.provider_alias_resolution import (
            canonical_provider_for_credential_record,
            normalize_canonical_provider,
        )
        from aethos_core.security.credential_vault import get_credential_vault

        requested = normalize_canonical_provider(provider) or (provider or "").strip().lower()
        rec = get_credential_vault().get(credential_id)
        record_canonical = canonical_provider_for_credential_record(rec) if rec else None
        if record_canonical and requested and record_canonical != requested:
            return {
                "ok": False,
                "credential_id": credential_id,
                "provider": provider,
                "credential_state": "invalid",
                "detail": f"Credential {credential_id} does not belong to provider {provider}.",
            }
    prov = provider or str(state_info.get("provider") or "")
    if require_validated and state_info.get("credential_state") != VALIDATED:
        detail = credential_gate_message(provider=prov, state_info=state_info)
        return {
            "ok": False,
            "credential_id": credential_id,
            "provider": prov,
            **state_info,
            "detail": detail,
        }
    if not state_info.get("decryptable"):
        detail = credential_gate_message(provider=prov, state_info=state_info)
        return {
            "ok": False,
            "credential_id": credential_id,
            "provider": prov,
            **state_info,
            "detail": detail,
        }
    return {"ok": True, "credential_id": credential_id, "provider": prov, **state_info}


def check_provider_credential_gate(
    provider: str,
    *,
    require_validated: bool = True,
) -> dict[str, Any]:
    from aethos_core.security.credential_vault import get_credential_vault

    from aethos_core.credentials.provider_alias_resolution import list_credentials_for_canonical

    creds = list_credentials_for_canonical(provider)
    if not creds:
        return {
            "ok": False,
            "provider": provider,
            "credential_state": "missing",
            "auth_source": "none",
            "detail": f"No {provider} credential configured.",
        }
    return check_credential_gate(
        creds[0].credential_id,
        provider=provider,
        require_validated=require_validated,
    )


def assert_usable_credential(
    *,
    provider: str,
    credential_id: str | None = None,
    operation_label: str = "provider operation",
) -> dict[str, Any]:
    if credential_id:
        gate = check_credential_gate(credential_id, provider=provider, require_validated=True)
    else:
        gate = check_provider_credential_gate(provider, require_validated=True)
    if not gate.get("ok"):
        gate["operation_label"] = operation_label
    return gate
