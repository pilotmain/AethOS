# SPDX-License-Identifier: Apache-2.0

from aethos_core.runtime.vercel_readonly_jobs import resolve_vercel_auth_for_chat
from aethos_core.runtime.browser_profile_store import browser_profile_store
from aethos_core.runtime.browser_profiles import PersistenceMode
from aethos_core.security.credential_vault import CredentialVault, reset_credential_vault_for_tests


def test_vercel_auth_falls_back_to_browser_when_no_token(tmp_path, monkeypatch):
    monkeypatch.setenv("CREDENTIALS_DIR", str(tmp_path / "credentials"))
    monkeypatch.setenv("BROWSER_AUTOMATION_ENABLED", "true")
    reset_credential_vault_for_tests()
    browser_profile_store.clear_all_for_tests()
    browser_profile_store.save_from_session(
        session_id="bsess-fb",
        site="vercel.com",
        storage_state={"cookies": [{"name": "s", "value": "1", "domain": ".vercel.com", "path": "/"}]},
        persistence_mode=PersistenceMode.PERSISTENT.value,
    )
    from aethos_core.config import get_settings

    get_settings.cache_clear()
    auth = resolve_vercel_auth_for_chat()
    assert auth["auth_method"] == "browser"
    assert auth["profile_id"]
    reset_credential_vault_for_tests()
    browser_profile_store.clear_all_for_tests()
