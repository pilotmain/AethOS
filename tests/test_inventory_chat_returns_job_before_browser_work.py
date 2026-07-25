# SPDX-License-Identifier: Apache-2.0

import os
from pathlib import Path

from fastapi.testclient import TestClient

from aethos_core.runtime.browser_diagnostics import set_playwright_runtime_override
from aethos_core.runtime.browser_profile_store import browser_profile_store
from aethos_core.runtime.browser_profiles import PersistenceMode
from tests.browser_test_utils import reset_browser_test_state


def test_chat_creates_inventory_job_when_runtime_blocked():
    from aethos_core.api.main import app

    os.environ["BROWSER_AUTOMATION_ENABLED"] = "true"
    reset_browser_test_state()
    browser_profile_store.save_from_session(
        session_id="bsess-chat",
        site="vercel.com",
        storage_state={"cookies": [], "origins": []},
        persistence_mode=PersistenceMode.PERSISTENT.value,
    )
    set_playwright_runtime_override(
        {
            "python_executable": "python",
            "playwright_package": "installed",
            "chromium_browser": "unknown",
            "launch_probe_ok": False,
            "launch_probe_error": "Playwright Sync API inside asyncio loop",
            "execution_ready": False,
            "runtime_error_kind": "asyncio_sync_api_misuse",
        }
    )
    try:
        from aethos_core.config import get_settings

        get_settings.cache_clear()
        client = TestClient(app)
        r = client.post(
            "/api/v1/chat",
            json={"message": "show my Vercel apps", "session_id": "runtime-block"},
        )
        assert r.status_code == 200
        body = r.json()
        reply = body["reply"].lower()
        assert "created tracked job" in reply
        assert "job-" in body["reply"]
        assert "bprof-" in body["reply"]
        assert body["intent"] == "vercel_readonly_job_created"
        assert (body.get("meta") or {}).get("proposed_job_id")
    finally:
        reset_browser_test_state()
