# SPDX-License-Identifier: Apache-2.0

from fastapi.testclient import TestClient

from tests.browser_test_utils import drain_browser_executor, reset_browser_test_state, use_mock_browser_driver


def test_since_event_id_returns_only_newer_events():
    from aethos_core.api.main import app

    use_mock_browser_driver(installed=True)
    try:
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
        all_events = client.get(f"/api/v1/browser/sessions/events?ids={sid}").json()["events"]
        assert len(all_events) >= 2
        cursor = all_events[0]["id"]
        after = client.get(
            f"/api/v1/browser/sessions/events?ids={sid}&since_event_id={cursor}",
        ).json()["events"]
        assert all(e["id"] != cursor for e in after)
        assert len(after) == len(all_events) - 1
    finally:
        reset_browser_test_state()
