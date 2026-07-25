# SPDX-License-Identifier: Apache-2.0

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def vault_env(tmp_path, monkeypatch):
    monkeypatch.setenv("CREDENTIALS_DIR", str(tmp_path / "credentials"))
    monkeypatch.setenv("TELEGRAM_ENABLED", "true")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "")
    from aethos_core.security.credential_vault import reset_credential_vault_for_tests

    reset_credential_vault_for_tests()
    from aethos_core.config import get_settings

    get_settings.cache_clear()
    yield tmp_path
    reset_credential_vault_for_tests()
    get_settings.cache_clear()


def test_telegram_bot_token_save_test_revoke(vault_env):
    from aethos_core.api.main import app

    with TestClient(app) as client:
        with patch(
            "aethos_core.channels.telegram.telegram_auth.test_bot_token",
            return_value={"ok": True, "detail": "Bot @aethos_bot verified.", "bot_username": "aethos_bot"},
        ):
            r = client.post(
                "/api/v1/channels/telegram/credentials",
                json={"label": "Primary bot", "token": "1234567890:ABCDEFghijklmnopqrstuvwxyz"},
            )
        assert r.status_code == 200
        body = r.json()
        assert body["ok"] is True
        assert "1234567890:ABCDEF" not in str(body)
        assert body["credential"]["masked_identifier"]

        status = client.get("/api/v1/channels/telegram/status").json()
        assert status["token_configured"] is True
        assert status["token_source"] == "vault"
        assert "1234567890" not in str(status)

        cred_id = body["credential"]["credential_id"]
        revoked = client.post(f"/api/v1/channels/telegram/credentials/{cred_id}/revoke").json()
        assert revoked["ok"] is True


def test_resolve_telegram_bot_token_prefers_vault(vault_env):
    from aethos_core.security.credential_vault import get_credential_vault
    from aethos_core.channels.telegram.telegram_token import resolve_telegram_bot_token

    vault = get_credential_vault()
    rec = vault.store_api_token(provider="telegram", label="Bot", token="1234567890:ABCDEFghijklmnopqrstuvwxyz", scope=[])
    token, cred_id = resolve_telegram_bot_token()
    assert token == "1234567890:ABCDEFghijklmnopqrstuvwxyz"
    assert cred_id == rec.credential_id
