# SPDX-License-Identifier: Apache-2.0

import pytest

from aethos_core.runtime.browser_profile_store import browser_profile_store
from aethos_core.runtime.browser_profiles import BrowserProfile, BrowserProfileStatus, PersistenceMode
from aethos_core.runtime.vercel_readonly_jobs import (
    _vercel_profile_sort_key,
    resolve_vercel_profile_for_chat,
)


@pytest.fixture
def isolated_profiles_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("BROWSER_PROFILES_DIR", str(tmp_path))
    from aethos_core.config import get_settings

    get_settings.cache_clear()
    browser_profile_store.clear_all_for_tests()
    yield tmp_path
    browser_profile_store.clear_all_for_tests()
    get_settings.cache_clear()


def test_sort_key_prefers_persistent_over_use_once():
    once = BrowserProfile(
        profile_id="bprof-once",
        site="vercel.com",
        scope="vercel",
        storage_path="/tmp/once.storage.json",
        persistence_mode=PersistenceMode.USE_ONCE.value,
    )
    persistent = BrowserProfile(
        profile_id="bprof-persist",
        site="vercel.com",
        scope="vercel",
        storage_path="/tmp/persist.storage.json",
        persistence_mode=PersistenceMode.PERSISTENT.value,
    )
    assert _vercel_profile_sort_key(persistent) < _vercel_profile_sort_key(once)


def test_resolve_uses_persistent_saved_profile(isolated_profiles_dir):
    saved = browser_profile_store.save_from_session(
        session_id="bsess-persist",
        site="vercel.com",
        storage_state={"cookies": [], "origins": []},
        persistence_mode=PersistenceMode.PERSISTENT.value,
    )
    pid, block = resolve_vercel_profile_for_chat()
    assert block is None
    assert pid == saved.profile_id
    assert browser_profile_store.get(pid).status == BrowserProfileStatus.ACTIVE
