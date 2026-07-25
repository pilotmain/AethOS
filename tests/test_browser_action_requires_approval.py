# SPDX-License-Identifier: Apache-2.0

from fastapi.testclient import TestClient

from tests.browser_test_utils import reset_browser_test_state, use_mock_browser_driver


def test_browser_action_starts_pending():
    from aethos_core.api.main import app

    client = TestClient(app)
    proposed = client.post(
        "/api/v1/actions/propose",
        json={
            "action_type": "browser_navigation_plan",
            "params": {"target": "vercel.com", "mode": "supervised"},
        },
    ).json()
    assert proposed["status"] == "pending"
    assert proposed["action_type"] == "browser_navigation_plan"
    reset_browser_test_state()


def test_browser_approve_opens_session_with_mock():
    from aethos_core.api.main import app
    use_mock_browser_driver(installed=True)
    try:
        client = TestClient(app)
        proposed = client.post(
            "/api/v1/actions/propose",
            json={
                "action_type": "browser_navigation_plan",
                "params": {"target": "vercel.com", "mode": "supervised"},
            },
        ).json()
        from tests.browser_test_utils import drain_browser_executor

        client.post(f"/api/v1/actions/{proposed['id']}/approve")
        drain_browser_executor()
        approved = client.get(f"/api/v1/actions/{proposed['id']}/status").json()["action"]
        assert approved["status"] == "completed"
        assert approved["params"].get("browser_session_id", "").startswith("bsess-")
        events = client.get(f"/api/v1/actions/events?ids={proposed['id']}").json()["events"]
        completed = [e for e in events if e["event_type"] == "action_completed"]
        assert completed
        assert "browser session opened" in completed[-1]["message"].lower()
    finally:
        reset_browser_test_state()


def test_browser_deny_emits_lifecycle_event():
    from aethos_core.api.main import app

    client = TestClient(app)
    proposed = client.post(
        "/api/v1/actions/propose",
        json={
            "action_type": "browser_login_required_notice",
            "params": {"target": "vercel.com", "login_required": True},
        },
    ).json()
    client.post(f"/api/v1/actions/{proposed['id']}/deny")
    events = client.get(f"/api/v1/actions/events?ids={proposed['id']}").json()["events"]
    denied = [e for e in events if e["event_type"] == "action_denied"]
    assert denied
    assert "browser" in denied[-1]["message"].lower()
    assert "no browser session" in denied[-1]["message"].lower()
    reset_browser_test_state()
