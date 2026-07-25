# SPDX-License-Identifier: Apache-2.0

from unittest.mock import patch

import pytest

from aethos_core.runtime.browser_profile_store import browser_profile_store
from aethos_core.runtime.browser_profiles import BrowserProfileStatus, PersistenceMode
from aethos_core.runtime.vercel_readonly_inspector import run_profile_session_check


@pytest.fixture
def isolated_profiles_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("BROWSER_PROFILES_DIR", str(tmp_path))
    from aethos_core.config import get_settings

    get_settings.cache_clear()
    browser_profile_store.clear_all_for_tests()
    yield
    browser_profile_store.clear_all_for_tests()
    get_settings.cache_clear()


def test_runtime_error_does_not_mark_profile_expired(isolated_profiles_dir):
    profile = browser_profile_store.save_from_session(
        session_id="bsess-rt",
        site="vercel.com",
        storage_state={"cookies": [], "origins": []},
        persistence_mode=PersistenceMode.PERSISTENT.value,
    )
    err = RuntimeError(
        "It looks like you are using Playwright Sync API inside the asyncio loop."
    )
    with patch(
        "aethos_core.runtime.vercel_readonly_inspector.run_readonly_inspection",
        side_effect=err,
    ):
        result = run_profile_session_check(profile.profile_id)

    assert result["ok"] is False
    assert result["profile_status"] == BrowserProfileStatus.ACTIVE.value
    assert result["runtime_status"] == "failed"
    reloaded = browser_profile_store.get(profile.profile_id)
    assert reloaded is not None
    assert reloaded.status == BrowserProfileStatus.ACTIVE
