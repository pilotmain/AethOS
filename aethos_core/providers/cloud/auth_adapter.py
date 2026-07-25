# SPDX-License-Identifier: Apache-2.0
"""Generic API-token auth adapter for cloud and SaaS providers."""

from __future__ import annotations

from typing import Any, Callable

from aethos_core.connections.credential_state import connection_api_token_status
from aethos_core.connections.models import AuthMethod, ProviderConnectionStatus
from aethos_core.providers.base.auth_adapter import AuthAdapter
from aethos_core.security.credential_vault import get_credential_vault


class ApiTokenAuthAdapter(AuthAdapter):
    """Vault-backed API token adapter with optional live validation callback."""

    def __init__(
        self,
        *,
        provider: str,
        validate_fn: Callable[[str], dict[str, Any]] | None = None,
        missing_detail: str = "",
    ) -> None:
        self.provider = provider
        self._validate_fn = validate_fn
        self._missing_detail = missing_detail or (
            f"{provider.title()} credentials not configured — add a token in Mission Control → Advanced settings → Credentials."
        )

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

    def resolve_best_auth_method(self, *, operation: str = "read") -> dict[str, Any]:
        _ = operation
        creds = self.list_credentials()
        if creds:
            cid = str(creds[0].get("credential_id") or creds[0].get("id") or "")
            if cid:
                return {"method": "api_token", "credential_id": cid, "detail": None}
        return {"method": None, "credential_id": None, "detail": self._missing_detail}

    def test_credential(self, credential_id: str) -> dict[str, Any]:
        rec = get_credential_vault().get(credential_id)
        if not rec or rec.provider != self.provider:
            raise KeyError(credential_id)
        secret = get_credential_vault().retrieve_secret(credential_id) or {}
        token = str(secret.get("token") or "").strip()
        if not token:
            return {"ok": False, "detail": "Credential secret missing or not decryptable."}
        if self._validate_fn is None:
            return {"ok": True, "detail": f"{self.provider.title()} token stored (live validation not configured)."}
        return self._validate_fn(token)

    def revoke_credential(self, credential_id: str) -> bool:
        return get_credential_vault().revoke(credential_id)

    def get_api_token(self, credential_id: str) -> str | None:
        # Read the secret straight from the vault by id. This adapter IS the vault-backed
        # leaf resolver — it must NOT delegate to provider_runtime.get_provider_api_token,
        # which calls back here (infinite recursion → "maximum recursion depth exceeded",
        # surfaced to operators as a bogus "Anthropic validation internal error").
        if not credential_id:
            return None
        vault = get_credential_vault()
        rec = vault.get(credential_id)
        if not rec or rec.provider != self.provider:
            return None
        secret = vault.retrieve_secret(credential_id) or {}
        token = str(secret.get("token") or "").strip()
        return token or None
