# SPDX-License-Identifier: Apache-2.0

from fastapi.testclient import TestClient

from tests.browser_test_utils import reset_browser_test_state, use_mock_browser_driver


def test_start_session_on_navigation_approve():
    from aethos_core.api.main import app
    mock = use_mock_browser_driver(installed=True)
    try:
        client = TestClient(app)
        from tests.browser_test_utils import drain_browser_executor

        proposed = client.post(
            "/api/v1/actions/propose",
            json={
                "action_type": "browser_navigation_plan",
                "params": {"target": "vercel.com", "mode": "supervised"},
            },
        ).json()
        approved = client.post(f"/api/v1/actions/{proposed['id']}/approve").json()
        drain_browser_executor()
        approved = client.get(f"/api/v1/actions/{proposed['id']}/status").json()["action"]
        assert approved["status"] == "completed"
        assert approved["params"].get("browser_session_id", "").startswith("bsess-")
        events = client.get(f"/api/v1/actions/events?ids={proposed['id']}").json()["events"]
        completed = [e for e in events if e["event_type"] == "action_completed"]
        assert completed
        assert "browser session opened" in completed[-1]["message"].lower()
        assert mock.opened_urls == ["https://vercel.com"]
        sessions = client.get("/api/v1/browser/sessions").json()
        assert sessions["active_session_count"] == 1
        assert sessions["active_session"]["status"] in {"running", "waiting_for_operator"}
    finally:
        reset_browser_test_state()
