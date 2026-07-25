# SPDX-License-Identifier: Apache-2.0

from fastapi.testclient import TestClient

from tests.browser_test_utils import reset_browser_test_state, use_mock_browser_driver


def test_approve_fails_when_playwright_missing():
    from aethos_core.api.main import app
    use_mock_browser_driver(installed=False)
    try:
        client = TestClient(app)
        proposed = client.post(
            "/api/v1/actions/propose",
            json={
                "action_type": "browser_navigation_plan",
                "params": {"target": "vercel.com"},
            },
        ).json()
        approved = client.post(f"/api/v1/actions/{proposed['id']}/approve").json()
        assert approved["status"] == "failed"
        events = client.get(f"/api/v1/actions/events?ids={proposed['id']}").json()["events"]
        failed = [e for e in events if e["event_type"] == "action_failed"]
        assert failed
        assert "runtime environment" in failed[-1]["message"].lower()
    finally:
        reset_browser_test_state()
