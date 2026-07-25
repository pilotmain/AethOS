# SPDX-License-Identifier: Apache-2.0

import pytest

from aethos_core.runtime.browser_profile_store import browser_profile_store
from aethos_core.runtime.browser_profiles import (
    PersistenceMode,
    is_profile_reusable_for_inspection,
)


@pytest.fixture
def isolated_profiles_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("BROWSER_PROFILES_DIR", str(tmp_path))
    from aethos_core.config import get_settings

    get_settings.cache_clear()
    browser_profile_store.clear_all_for_tests()
    yield
    browser_profile_store.clear_all_for_tests()
    get_settings.cache_clear()


def test_use_once_profile_not_reusable(isolated_profiles_dir):
    p = browser_profile_store.save_from_session(
        session_id="bsess-once",
        site="vercel.com",
        storage_state={"cookies": []},
        persistence_mode=PersistenceMode.USE_ONCE.value,
    )
    assert is_profile_reusable_for_inspection(p) is False
    assert browser_profile_store.find_active_for_scope("vercel") is None


def test_persistent_profile_reusable(isolated_profiles_dir):
    p = browser_profile_store.save_from_session(
        session_id="bsess-perm",
        site="vercel.com",
        storage_state={"cookies": []},
        persistence_mode=PersistenceMode.PERSISTENT.value,
    )
    assert is_profile_reusable_for_inspection(p) is True
    assert browser_profile_store.find_active_for_scope("vercel") is not None


def test_timed_modes_set_expires_at(isolated_profiles_dir):
    p7 = browser_profile_store.save_from_session(
        session_id="bsess-7",
        site="vercel.com",
        storage_state={"cookies": []},
        persistence_mode=PersistenceMode.EXPIRES_7D.value,
    )
    assert p7.expires_at is not None
    assert p7.persistence_mode == PersistenceMode.EXPIRES_7D.value
