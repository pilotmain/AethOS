# SPDX-License-Identifier: Apache-2.0

import pytest

from aethos_core.providers.vercel.auth import VercelAuthAdapter
from aethos_core.runtime.browser_profile_store import browser_profile_store
from aethos_core.runtime.browser_profiles import PersistenceMode
from aethos_core.security.credential_vault import CredentialVault, reset_credential_vault_for_tests


@pytest.fixture
def env(tmp_path, monkeypatch):
    monkeypatch.setenv("CREDENTIALS_DIR", str(tmp_path / "credentials"))
    monkeypatch.setenv("BROWSER_AUTOMATION_ENABLED", "true")
    reset_credential_vault_for_tests()
    browser_profile_store.clear_all_for_tests()
    from aethos_core.config import get_settings

    get_settings.cache_clear()
    yield tmp_path
    reset_credential_vault_for_tests()
    browser_profile_store.clear_all_for_tests()
    get_settings.cache_clear()


def test_vercel_auth_resolution_prefers_api_token(env):
    CredentialVault(env / "credentials").store_api_token(
        provider="vercel",
        label="Primary",
        token="vercel_test_token_1234567890",
    )
    resolved = VercelAuthAdapter().resolve_best_auth_method(operation="read_projects")
    assert resolved["method"] == "api_token"


def test_vercel_auth_falls_back_to_browser(env):
    browser_profile_store.save_from_session(
        session_id="bsess-fallback",
        site="vercel.com",
        storage_state={"cookies": [{"name": "s", "value": "1", "domain": ".vercel.com", "path": "/"}]},
        persistence_mode=PersistenceMode.PERSISTENT.value,
    )
    resolved = VercelAuthAdapter().resolve_best_auth_method(operation="read_projects")
    assert resolved["method"] == "browser"
    assert resolved["profile_id"]
