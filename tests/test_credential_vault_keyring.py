# SPDX-License-Identifier: Apache-2.0

import pytest

from aethos_core.security.credential_vault import CredentialVault, reset_credential_vault_for_tests


@pytest.fixture
def vault(tmp_path, monkeypatch):
    monkeypatch.setenv("CREDENTIALS_DIR", str(tmp_path / "credentials"))
    reset_credential_vault_for_tests()
    from aethos_core.config import get_settings

    get_settings.cache_clear()
    v = CredentialVault(tmp_path / "credentials")
    yield v
    reset_credential_vault_for_tests()
    get_settings.cache_clear()


def test_credential_vault_stores_and_retrieves_api_token(vault):
    rec = vault.store_api_token(provider="vercel", label="Primary", token="vercel_test_token_1234567890")
    secret = vault.retrieve_secret(rec.credential_id)
    assert secret is not None
    assert secret["token"] == "vercel_test_token_1234567890"
    public = rec.to_public_dict()
    assert "vercel_test_token_1234567890" not in str(public)
    assert public["masked_identifier"]


def test_credential_vault_revoke_removes_secret(vault):
    rec = vault.store_api_token(
        provider="vercel",
        label="Primary",
        token="vercel_revoke_me_123456789",  # gitleaks:allow - synthetic fixture
    )
    assert vault.revoke(rec.credential_id)
    assert vault.get(rec.credential_id) is None
    assert vault.retrieve_secret(rec.credential_id) is None
