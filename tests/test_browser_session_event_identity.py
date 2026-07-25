# SPDX-License-Identifier: Apache-2.0

from fastapi.testclient import TestClient

from tests.browser_test_utils import drain_browser_executor, reset_browser_test_state, use_mock_browser_driver


def test_browser_session_event_ids_stable_across_polls():
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
        first = client.get(f"/api/v1/browser/sessions/events?ids={sid}").json()["events"]
        second = client.get(f"/api/v1/browser/sessions/events?ids={sid}").json()["events"]
        assert len(first) == len(second) >= 2
        assert [e["id"] for e in first] == [e["id"] for e in second]
        assert all(e.get("event_id") == e["id"] for e in first)
    finally:
        reset_browser_test_state()


def test_open_event_created_once_not_on_heartbeat():
    from aethos_core.api.main import app
    from aethos_core.runtime.browser_session import browser_session_store

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
        before = client.get(f"/api/v1/browser/sessions/events?ids={sid}").json()["events"]
        running = [e for e in before if e["event_type"] == "session_running"]
        assert len(running) == 1
        browser_session_store.tick_heartbeats()
        browser_session_store.tick_heartbeats()
        after = client.get(f"/api/v1/browser/sessions/events?ids={sid}").json()["events"]
        running_after = [e for e in after if e["event_type"] == "session_running"]
        assert len(running_after) == 1
        assert running[0]["id"] == running_after[0]["id"]
    finally:
        reset_browser_test_state()
