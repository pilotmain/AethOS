# SPDX-License-Identifier: Apache-2.0
"""Telegram bot token auth — credential vault backed."""

from __future__ import annotations

from typing import Any

from aethos_core.channels.telegram.telegram_transport import test_bot_token
from aethos_core.connections.models import AuthMethod, ProviderConnectionStatus
from aethos_core.providers.base.auth_adapter import AuthAdapter
from aethos_core.security.credential_vault import get_credential_vault


class TelegramAuthAdapter(AuthAdapter):
    provider = "telegram"

    def list_credentials(self) -> list[dict[str, Any]]:
        return [c.to_public_dict() for c in get_credential_vault().list_credentials(provider=self.provider)]

    def connection_status(self) -> ProviderConnectionStatus:
        from aethos_core.config import get_settings

        vault = get_credential_vault()
        creds = vault.list_credentials(provider=self.provider)
        api_token = "missing"
        if creds and any(not c.revoked for c in creds):
            api_token = "configured"
        elif get_settings().telegram_bot_token.strip():
            api_token = "configured"
        return ProviderConnectionStatus(
            provider=self.provider,
            preferred_method=AuthMethod.API_TOKEN,
            api_token=api_token,
            browser_session="missing",
            cli_auth="not_detected",
            username_password="missing",
            credentials=self.list_credentials(),
        )

    def resolve_best_auth_method(self, *, operation: str = "send_message") -> dict[str, Any]:
        from aethos_core.channels.telegram.telegram_token import resolve_telegram_bot_token

        token, cred_id = resolve_telegram_bot_token()
        if not token:
            return {
                "method": None,
                "credential_id": None,
                "detail": "No Telegram bot token configured. Add one in Mission Control → Advanced settings → Credentials → Telegram.",
            }
        return {"method": AuthMethod.API_TOKEN.value, "credential_id": cred_id, "detail": None}

    def test_credential(self, credential_id: str) -> dict[str, Any]:
        vault = get_credential_vault()
        secret = vault.retrieve_secret(credential_id)
        token = str((secret or {}).get("token") or "").strip()
        if not token:
            return {"ok": False, "detail": "Credential secret missing."}
        result = test_bot_token(token=token)
        vault.mark_test_result(credential_id, ok=bool(result.get("ok")))
        return result

    def revoke_credential(self, credential_id: str) -> bool:
        return get_credential_vault().revoke(credential_id)
