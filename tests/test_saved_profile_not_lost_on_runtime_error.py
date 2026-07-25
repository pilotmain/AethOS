# SPDX-License-Identifier: Apache-2.0

from aethos_core.runtime.browser_diagnostics import BrowserRuntimeNotReady, set_playwright_runtime_override
from aethos_core.runtime.browser_profile_store import browser_profile_store
from aethos_core.runtime.browser_profiles import BrowserProfileStatus, PersistenceMode
from aethos_core.runtime.vercel_readonly_jobs import (
    latest_saved_vercel_profile,
    resolve_vercel_profile_for_chat,
)
from tests.browser_test_utils import reset_browser_test_state


def test_runtime_error_does_not_hide_saved_profile(tmp_path, monkeypatch):
    monkeypatch.setenv("BROWSER_PROFILES_DIR", str(tmp_path))
    from aethos_core.config import get_settings

    get_settings.cache_clear()
    browser_profile_store.clear_all_for_tests()
    profile = browser_profile_store.save_from_session(
        session_id="bsess-runtime",
        site="vercel.com",
        storage_state={"cookies": [], "origins": []},
        persistence_mode=PersistenceMode.PERSISTENT.value,
    )
    fake = {
        "python_executable": "python",
        "playwright_package": "installed",
        "chromium_browser": "unknown",
        "launch_probe_ok": False,
        "launch_probe_error": "Playwright Sync API inside asyncio loop",
        "execution_ready": False,
        "runtime_error_kind": "asyncio_sync_api_misuse",
    }
    set_playwright_runtime_override(fake)
    try:
        pid, block = resolve_vercel_profile_for_chat()
        assert block is None
        assert pid == profile.profile_id
        saved = latest_saved_vercel_profile()
        assert saved is not None
        assert saved.status == BrowserProfileStatus.ACTIVE
        from aethos_core.runtime.browser_diagnostics import validate_browser_runtime_for_execution

        try:
            validate_browser_runtime_for_execution()
        except BrowserRuntimeNotReady:
            pass
        assert browser_profile_store.get(profile.profile_id).status == BrowserProfileStatus.ACTIVE
    finally:
        reset_browser_test_state()
