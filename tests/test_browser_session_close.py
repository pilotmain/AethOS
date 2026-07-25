# SPDX-License-Identifier: Apache-2.0

from fastapi.testclient import TestClient

from tests.browser_test_utils import reset_browser_test_state, use_mock_browser_driver


def test_close_browser_session_via_api():
    from aethos_core.api.main import app
    mock = use_mock_browser_driver(installed=True)
    try:
        client = TestClient(app)
        proposed = client.post(
            "/api/v1/actions/propose",
            json={
                "action_type": "browser_navigation_plan",
                "params": {"target": "vercel.com"},
            },
        ).json()
        from tests.browser_test_utils import drain_browser_executor

        client.post(f"/api/v1/actions/{proposed['id']}/approve")
        drain_browser_executor()
        active = client.get("/api/v1/browser/sessions").json()["active_session"]
        assert active is not None
        sid = active["id"]
        closed = client.post(f"/api/v1/browser/sessions/{sid}/close").json()["session"]
        assert closed["status"] == "completed"
        assert mock.closed_count >= 1
        assert client.get("/api/v1/browser/sessions").json()["active_session_count"] == 0
    finally:
        reset_browser_test_state()
