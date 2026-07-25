# SPDX-License-Identifier: Apache-2.0

from fastapi.testclient import TestClient

from tests.browser_test_utils import drain_browser_executor, reset_browser_test_state, use_mock_browser_driver


def test_browser_session_events_endpoint():
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
        events = client.get(f"/api/v1/browser/sessions/events?ids={sid}").json()["events"]
        types = [e["event_type"] for e in events]
        assert "session_launching" in types or "session_running" in types
    finally:
        reset_browser_test_state()


def test_terminate_emits_completed_event():
    from aethos_core.api.main import app

    use_mock_browser_driver(installed=True)
    try:
        client = TestClient(app)
        proposed = client.post(
            "/api/v1/actions/propose",
            json={"action_type": "browser_navigation_plan", "params": {"target": "github.com"}},
        ).json()
        client.post(f"/api/v1/actions/{proposed['id']}/approve")
        drain_browser_executor()
        sid = client.get(f"/api/v1/actions/{proposed['id']}/status").json()["action"]["params"][
            "browser_session_id"
        ]
        closed = client.post(f"/api/v1/browser/sessions/{sid}/terminate").json()["session"]
        assert closed["status"] == "completed"
    finally:
        reset_browser_test_state()


def test_multiple_sessions_unique_ids():
    from aethos_core.api.main import app

    use_mock_browser_driver(installed=True)
    try:
        client = TestClient(app)
        ids = []
        for target in ("vercel.com", "github.com"):
            proposed = client.post(
                "/api/v1/actions/propose",
                json={
                    "action_type": "browser_navigation_plan",
                    "params": {"target": target},
                },
            ).json()
            client.post(f"/api/v1/actions/{proposed['id']}/approve")
            drain_browser_executor()
            sid = client.get(f"/api/v1/actions/{proposed['id']}/status").json()["action"]["params"][
                "browser_session_id"
            ]
            ids.append(sid)
            client.post(f"/api/v1/browser/sessions/{sid}/terminate")
        assert len(set(ids)) == 2
    finally:
        reset_browser_test_state()
