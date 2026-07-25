# SPDX-License-Identifier: Apache-2.0

from fastapi.testclient import TestClient

from tests.browser_test_utils import drain_browser_executor, reset_browser_test_state, use_mock_browser_driver


def test_save_requires_active_session_not_auto():
    from aethos_core.api.main import app
    from aethos_core.runtime.browser_profile_store import browser_profile_store

    browser_profile_store.clear_all_for_tests()
    client = TestClient(app)
    r = client.post(
        "/api/v1/browser/profiles/save",
        json={"session_id": "bsess-missing"},
    )
    assert r.status_code in {404, 409}
    assert browser_profile_store.list_all() == []


def test_save_after_supervised_session_explicit():
    from aethos_core.api.main import app
    from aethos_core.runtime.browser_profile_store import browser_profile_store

    use_mock_browser_driver(installed=True)
    try:
        browser_profile_store.clear_all_for_tests()
        client = TestClient(app)
        proposed = client.post(
            "/api/v1/actions/propose",
            json={
                "action_type": "browser_navigation_plan",
                "params": {"target": "vercel.com"},
            },
        ).json()
        client.post(f"/api/v1/actions/{proposed['id']}/approve")
        drain_browser_executor()
        sid = client.get(f"/api/v1/actions/{proposed['id']}/status").json()["action"]["params"][
            "browser_session_id"
        ]
        saved = client.post(
            "/api/v1/browser/profiles/save",
            json={"session_id": sid},
        ).json()
        assert saved["ok"] is True
        assert saved["saved"] is True
        assert saved["profile"]["site"] == "vercel.com"
        assert "password" not in str(saved).lower()
        profiles = client.get("/api/v1/browser/profiles").json()["profiles"]
        assert len(profiles) == 1
    finally:
        reset_browser_test_state()
