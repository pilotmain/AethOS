# SPDX-License-Identifier: Apache-2.0

from fastapi.testclient import TestClient

from tests.browser_test_utils import drain_browser_executor, reset_browser_test_state, use_mock_browser_driver


def test_save_active_session_success():
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
        )
        assert saved.status_code == 200
        body = saved.json()
        assert body["ok"] is True
        assert body["saved"] is True
        assert body["profile"]["site"] == "vercel.com"
        profiles = client.get("/api/v1/browser/profiles").json()["profiles"]
        assert len(profiles) == 1
    finally:
        reset_browser_test_state()


def test_double_save_idempotent():
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
        first = client.post("/api/v1/browser/profiles/save", json={"session_id": sid}).json()
        second = client.post("/api/v1/browser/profiles/save", json={"session_id": sid}).json()
        assert first["profile"]["profile_id"] == second["profile"]["profile_id"]
    finally:
        reset_browser_test_state()
