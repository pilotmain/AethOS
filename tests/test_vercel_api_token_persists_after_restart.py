# SPDX-License-Identifier: Apache-2.0

import pytest

from aethos_core.security.credential_vault import CredentialVault, get_credential_vault, reset_credential_vault_for_tests


@pytest.fixture
def vault_paths(tmp_path, monkeypatch):
    cred_dir = tmp_path / "credentials"
    monkeypatch.setenv("CREDENTIALS_DIR", str(cred_dir))
    reset_credential_vault_for_tests()
    from aethos_core.config import get_settings

    get_settings.cache_clear()
    yield cred_dir
    reset_credential_vault_for_tests()
    get_settings.cache_clear()


def test_vercel_api_token_persists_after_restart(vault_paths):
    v1 = CredentialVault(vault_paths)
    rec = v1.store_api_token(
        provider="vercel",
        label="Primary",
        token="vercel_test_token_persist_1234567890",
    )
    reset_credential_vault_for_tests()
    v2 = get_credential_vault()
    loaded = v2.get(rec.credential_id)
    assert loaded is not None
    secret = v2.retrieve_secret(rec.credential_id)
    assert secret is not None
    assert secret["token"] == "vercel_test_token_persist_1234567890"
