# SPDX-License-Identifier: Apache-2.0
"""Resolve Telegram bot token — vault first, env fallback."""

from __future__ import annotations

import logging

from aethos_core.config import get_settings
from aethos_core.security.credential_vault import get_credential_vault

_log = logging.getLogger(__name__)

# Bot tokens are ``<bot_id>:<secret>`` — garbage vault rows must not shadow a good .env token.
_MIN_TELEGRAM_TOKEN_LEN = 35


def _looks_like_telegram_bot_token(token: str) -> bool:
    text = (token or "").strip()
    if len(text) < _MIN_TELEGRAM_TOKEN_LEN or ":" not in text:
        return False
    bot_id, secret = text.split(":", 1)
    return bot_id.isdigit() and len(secret) >= 20


def resolve_telegram_bot_token() -> tuple[str, str | None]:
    """Return (token, credential_id). credential_id is None for env fallback."""
    vault = get_credential_vault()
    creds = [c for c in vault.list_credentials(provider="telegram") if not c.revoked]
    if creds:
        creds.sort(key=lambda c: c.last_used_at or c.created_at, reverse=True)
        for cred in creds:
            secret = vault.retrieve_secret(cred.credential_id)
            token = str((secret or {}).get("token") or "").strip()
            if _looks_like_telegram_bot_token(token):
                return token, cred.credential_id
            if token:
                _log.warning(
                    "telegram_vault_token_invalid credential_id=%s len=%d — skipping to env fallback",
                    cred.credential_id,
                    len(token),
                )
    env_token = get_settings().telegram_bot_token.strip()
    if _looks_like_telegram_bot_token(env_token):
        return env_token, None
    return "", None
