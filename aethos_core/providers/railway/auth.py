# SPDX-License-Identifier: Apache-2.0
"""Railway auth adapter — API token via credential vault."""

from __future__ import annotations

from typing import Any

from aethos_core.connections.credential_state import connection_api_token_status
from aethos_core.connections.models import AuthMethod, ProviderConnectionStatus
from aethos_core.providers.base.auth_adapter import AuthAdapter
from aethos_core.security.credential_vault import get_credential_vault


class RailwayAuthAdapter(AuthAdapter):
    provider = "railway"

    def list_credentials(self) -> list[dict[str, Any]]:
        return [c.to_public_dict() for c in get_credential_vault().list_credentials(provider=self.provider)]

    def connection_status(self) -> ProviderConnectionStatus:
        api_token = connection_api_token_status(provider=self.provider)
        return ProviderConnectionStatus(
            provider=self.provider,
            preferred_method=AuthMethod.API_TOKEN,
            api_token=api_token,
            browser_session="missing",
            cli_auth="not_detected",
            username_password="missing",
            credentials=self.list_credentials(),
        )

    def resolve_best_auth_method(self, *, operation: str = "read_projects") -> dict[str, Any]:
        _ = operation
        cred = self._latest_api_token()
        if not cred:
            return {
                "method": None,
                "credential_id": None,
                "detail": "No Railway API token configured. Add one in Mission Control → Advanced settings → Credentials.",
            }
        return {"method": "api_token", "credential_id": cred.credential_id, "profile_id": None, "detail": None}

    def _latest_api_token(self):
        from aethos_core.connections.credential_state import resolve_credential_state
        from aethos_core.credentials.provider_alias_resolution import list_credentials_for_canonical

        creds = list_credentials_for_canonical(self.provider)
        for cred in creds:
            if cred.revoked or cred.type.value != "api_token":
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
