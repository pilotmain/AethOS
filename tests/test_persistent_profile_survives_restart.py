# SPDX-License-Identifier: Apache-2.0

import pytest

from aethos_core.runtime.browser_profile_store import BrowserProfileStore, browser_profile_store
from aethos_core.runtime.browser_profiles import BrowserProfileStatus, PersistenceMode


@pytest.fixture
def isolated_profiles_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("BROWSER_PROFILES_DIR", str(tmp_path))
    from aethos_core.config import get_settings

    get_settings.cache_clear()
    browser_profile_store.clear_all_for_tests()
    yield tmp_path
    browser_profile_store.clear_all_for_tests()
    get_settings.cache_clear()


def test_persistent_profile_survives_store_recreate(isolated_profiles_dir):
    saved = browser_profile_store.save_from_session(
        session_id="bsess-persist",
        site="vercel.com",
        storage_state={"cookies": [], "origins": []},
        persistence_mode=PersistenceMode.PERSISTENT.value,
    )
    pid = saved.profile_id

    fresh = BrowserProfileStore()
    loaded = fresh.get(pid)
    assert loaded is not None
    assert loaded.persistence_mode == PersistenceMode.PERSISTENT.value
    assert loaded.status == BrowserProfileStatus.ACTIVE
    assert fresh.find_active_for_scope("vercel") is not None
