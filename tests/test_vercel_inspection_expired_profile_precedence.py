# SPDX-License-Identifier: Apache-2.0

import pytest

from aethos_core.runtime.browser_profile_store import browser_profile_store
from aethos_core.runtime.browser_profiles import BrowserProfileStatus
from aethos_core.runtime.browser_readiness import ProfileExpiredError, preflight_readonly_profile
from tests.browser_test_utils import use_mock_browser_driver


@pytest.fixture
def profiles_env(tmp_path, monkeypatch):
    monkeypatch.setenv("BROWSER_PROFILES_DIR", str(tmp_path))
    from aethos_core.config import get_settings

    get_settings.cache_clear()
    browser_profile_store.clear_all_for_tests()
    yield
    browser_profile_store.clear_all_for_tests()
    get_settings.cache_clear()


def test_expired_profile_raises_before_browser_runtime(profiles_env, monkeypatch):
    use_mock_browser_driver(installed=False)

    def fail_runtime():
        raise AssertionError("browser runtime must not be checked when profile is expired")

    monkeypatch.setattr(
        "aethos_core.runtime.browser_readiness.validate_browser_runtime_for_execution",
        fail_runtime,
    )
    pid = browser_profile_store.save_from_session(
        session_id="s1",
        site="vercel.com",
        storage_state={},
    ).profile_id
    browser_profile_store.set_status(pid, BrowserProfileStatus.EXPIRED)
    with pytest.raises(ProfileExpiredError) as exc:
        preflight_readonly_profile(pid)
    assert "expired" in str(exc.value).lower()
