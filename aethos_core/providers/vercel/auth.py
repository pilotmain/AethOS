# SPDX-License-Identifier: Apache-2.0
"""Vercel authentication adapter — API token, browser session, CLI."""

from __future__ import annotations

import shutil
from typing import Any

from aethos_core.connections.credential_state import connection_api_token_status
from aethos_core.providers.base.auth_adapter import AuthAdapter
from aethos_core.connections.models import AuthMethod, ProviderConnectionStatus
from aethos_core.runtime.vercel_readonly_jobs import (
    latest_reusable_vercel_profile,
    latest_saved_vercel_profile,
)
from aethos_core.security.credential_vault import get_credential_vault


class VercelAuthAdapter(AuthAdapter):
    provider = "vercel"

    def list_credentials(self) -> list[dict[str, Any]]:
        return [c.to_public_dict() for c in get_credential_vault().list_credentials(provider=self.provider)]

    def connection_status(self) -> ProviderConnectionStatus:
        vault = get_credential_vault()
        api_token = connection_api_token_status(provider=self.provider)
        reusable = latest_reusable_vercel_profile()
        saved = latest_saved_vercel_profile()
        if reusable:
            browser = "saved"
        elif saved:
            browser = "expired"
        else:
            browser = "missing"
        cli = "detected" if shutil.which("vercel") else "not_detected"
        preferred_raw = vault.get_preferred_method(self.provider)
        try:
            preferred = AuthMethod(preferred_raw)
        except ValueError:
            preferred = AuthMethod.ASK
        return ProviderConnectionStatus(
            provider=self.provider,
            preferred_method=preferred,
            api_token=api_token,
            browser_session=browser,
            cli_auth=cli,
            username_password="missing",
            credentials=self.list_credentials(),
        )

    def resolve_best_auth_method(self, *, operation: str = "read_projects") -> dict[str, Any]:
        status = self.connection_status()
        preferred = status.preferred_method
        order: list[AuthMethod]
        if preferred == AuthMethod.API_TOKEN:
            order = [AuthMethod.API_TOKEN, AuthMethod.CLI, AuthMethod.BROWSER]
        elif preferred == AuthMethod.BROWSER:
            order = [AuthMethod.BROWSER, AuthMethod.API_TOKEN, AuthMethod.CLI]
        elif preferred == AuthMethod.CLI:
            order = [AuthMethod.CLI, AuthMethod.API_TOKEN, AuthMethod.BROWSER]
        else:
            order = [AuthMethod.API_TOKEN, AuthMethod.CLI, AuthMethod.BROWSER]

        for method in order:
            resolved = self._resolve_method(method, operation=operation)
            if resolved:
                return resolved

        # Validated API token is authoritative for read-only ops even when preferred
        # is "ask" and no browser/cli path is usable.
        api_cred = self._latest_api_token()
        if api_cred and str(status.api_token) == "validated":
            return {
                "method": "api_token",
                "credential_id": api_cred.credential_id,
                "profile_id": None,
            }
        return {
            "method": None,
            "credential_id": None,
            "profile_id": None,
            "detail": "No Vercel auth configured. Add an API token in Mission Control → Advanced settings → Credentials.",
        }

    def _resolve_method(self, method: AuthMethod, *, operation: str) -> dict[str, Any] | None:
        _ = operation
        if method == AuthMethod.API_TOKEN:
            cred = self._latest_api_token()
            if cred:
                return {"method": "api_token", "credential_id": cred.credential_id, "profile_id": None}
        if method == AuthMethod.BROWSER:
            profile = latest_reusable_vercel_profile() or latest_saved_vercel_profile()
            if profile:
                return {"method": "browser", "credential_id": None, "profile_id": profile.profile_id}
        if method == AuthMethod.CLI:
            return None
        return None

    def _latest_api_token(self):
        from aethos_core.connections.credential_state import resolve_credential_state

        creds = get_credential_vault().list_credentials(provider=self.provider)
        for cred in creds:
            if cred.type.value != "api_token":
                continue
            state = resolve_credential_state(cred.credential_id)
            if state.get("decryptable"):
                return cred
        return None

    def test_credential(self, credential_id: str) -> dict[str, Any]:
        rec = get_credential_vault().get(credential_id)
        if not rec or rec.provider != self.provider:
            raise KeyError(credential_id)
        from aethos_core.connections.credential_validation import validate_provider_credential

        return validate_provider_credential(provider=self.provider, credential_id=credential_id)

    def revoke_credential(self, credential_id: str) -> bool:
        return get_credential_vault().revoke(credential_id)

    def get_api_token(self, credential_id: str) -> str:
        secret = get_credential_vault().retrieve_secret(credential_id) or {}
        return str(secret.get("token") or "")

    def capabilities_for_credential(self, credential_id: str) -> dict[str, Any]:
        rec = get_credential_vault().get(credential_id)
        if not rec:
            raise KeyError(credential_id)
        return {
            "provider": self.provider,
            "type": rec.type.value,
            "scope": list(rec.scope),
            "write_allowed": rec.write_allowed,
        }
