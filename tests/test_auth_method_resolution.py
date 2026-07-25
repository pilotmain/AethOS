# SPDX-License-Identifier: Apache-2.0

import pytest

from aethos_core.providers.vercel.auth import VercelAuthAdapter
from aethos_core.security.credential_vault import CredentialVault, reset_credential_vault_for_tests


@pytest.fixture
def vault(tmp_path, monkeypatch):
    monkeypatch.setenv("CREDENTIALS_DIR", str(tmp_path / "credentials"))
    reset_credential_vault_for_tests()
    from aethos_core.config import get_settings

    get_settings.cache_clear()
    v = CredentialVault(tmp_path / "credentials")
    v.store_api_token(provider="vercel", label="Primary", token="vercel_test_token_1234567890")
    yield
    reset_credential_vault_for_tests()
    get_settings.cache_clear()


def test_auth_method_resolution_prefers_api_token(vault, monkeypatch):
    monkeypatch.setenv("BROWSER_AUTOMATION_ENABLED", "false")
    from aethos_core.config import get_settings

    get_settings.cache_clear()
    resolved = VercelAuthAdapter().resolve_best_auth_method(operation="read_projects")
    assert resolved["method"] == "api_token"
    assert resolved["credential_id"]
