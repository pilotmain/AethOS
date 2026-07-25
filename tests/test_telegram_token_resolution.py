# SPDX-License-Identifier: Apache-2.0
"""Telegram bot token resolution — vault vs env."""

from __future__ import annotations

from aethos_core.channels.telegram.telegram_token import _looks_like_telegram_bot_token, resolve_telegram_bot_token

_SYNTHETIC_VALID_TOKEN = "1234567890:TEST_TOKEN_FOR_AETHOS_123456789ABCDE"


def test_looks_like_telegram_bot_token():
    assert _looks_like_telegram_bot_token(_SYNTHETIC_VALID_TOKEN)
    assert not _looks_like_telegram_bot_token("short")
    assert not _looks_like_telegram_bot_token("123456789:toosmall")


def test_resolve_prefers_valid_vault_over_env(monkeypatch, tmp_path):
    from aethos_core.config import get_settings
    from aethos_core.security.credential_vault import CredentialVault, reset_credential_vault_for_tests

    monkeypatch.setenv("CREDENTIALS_DIR", str(tmp_path / "credentials"))
    get_settings.cache_clear()
    reset_credential_vault_for_tests()
    vault = CredentialVault()
    good = _SYNTHETIC_VALID_TOKEN
    rec = vault.store_api_token(provider="telegram", label="bot", token=good)
    monkeypatch.setenv(
        "TELEGRAM_BOT_TOKEN",
        "9999999999:AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",  # gitleaks:allow - fixture
    )
    get_settings.cache_clear()
    token, cred_id = resolve_telegram_bot_token()
    assert token == good
    assert cred_id == rec.credential_id
    get_settings.cache_clear()


def test_resolve_skips_corrupt_vault_token(monkeypatch, tmp_path):
    from aethos_core.config import get_settings
    from aethos_core.security.credential_vault import CredentialVault, reset_credential_vault_for_tests

    monkeypatch.setenv("CREDENTIALS_DIR", str(tmp_path / "credentials"))
    env_good = _SYNTHETIC_VALID_TOKEN
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", env_good)
    get_settings.cache_clear()
    reset_credential_vault_for_tests()
    vault = CredentialVault()
    bad_rec = vault.store_api_token(provider="telegram", label="bad", token="1234567890:short")
    get_settings.cache_clear()
    token, cred_id = resolve_telegram_bot_token()
    assert token == env_good
    assert cred_id is None
    assert bad_rec.credential_id
    get_settings.cache_clear()
