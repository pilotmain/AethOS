# SPDX-License-Identifier: Apache-2.0

import os

from fastapi.testclient import TestClient

from aethos_core.runtime.browser_profile_store import browser_profile_store
from aethos_core.runtime.browser_profiles import BrowserProfileStatus
from tests.browser_test_utils import reset_browser_test_state, use_mock_browser_driver


def test_chat_expired_profile_no_job():
    from aethos_core.api.main import app

    use_mock_browser_driver(installed=True)
    os.environ["BROWSER_AUTOMATION_ENABLED"] = "true"
    browser_profile_store.clear_all_for_tests()
    pid = browser_profile_store.save_from_session(
        session_id="bsess-exp",
        site="vercel.com",
        storage_state={"cookies": []},
    ).profile_id
    browser_profile_store.set_status(pid, BrowserProfileStatus.EXPIRED)
    try:
        from aethos_core.config import get_settings

        get_settings.cache_clear()
        client = TestClient(app)
        r = client.post(
            "/api/v1/chat",
            json={"message": "show my Vercel apps", "session_id": "exp-prof"},
        )
        body = r.json()
        assert body["used_llm"] is False
        reply = body["reply"].lower()
        assert "expired" in reply
        assert "approved saved session" not in reply
        assert (body.get("meta") or {}).get("proposed_job_id") is None
    finally:
        reset_browser_test_state()


def test_chromium_failure_does_not_mark_profile_expired(monkeypatch):
    use_mock_browser_driver(installed=True)
    browser_profile_store.clear_all_for_tests()
    pid = browser_profile_store.save_from_session(
        session_id="bsess-ok",
        site="vercel.com",
        storage_state={"cookies": []},
    ).profile_id
    from aethos_core.runtime.vercel_readonly_inspector import run_profile_session_check

    monkeypatch.setattr(
        "aethos_core.runtime.vercel_readonly_inspector.run_readonly_inspection",
        lambda **kw: (_ for _ in ()).throw(
            RuntimeError(
                "Chromium browser is not installed for Playwright in the AethOS runtime environment."
            )
        ),
    )
    result = run_profile_session_check(pid)
    assert result["ok"] is False
    assert "chromium" in result["message"].lower()
    profile = browser_profile_store.get(pid)
    assert profile is not None
    assert profile.status == BrowserProfileStatus.ACTIVE
    reset_browser_test_state()
