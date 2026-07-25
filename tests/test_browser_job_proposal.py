# SPDX-License-Identifier: Apache-2.0

from fastapi.testclient import TestClient

from tests.browser_test_utils import reset_browser_test_state, use_mock_browser_driver


def test_propose_browser_navigation_via_api():
    from aethos_core.api.main import app

    client = TestClient(app)
    r = client.post(
        "/api/v1/browser/jobs/propose",
        json={
            "message": "open vercel.com in browser automation",
            "session_id": "br-prop-api",
        },
    )
    assert r.status_code == 200
    action = r.json()["action"]
    assert action["status"] == "pending"
    assert action["action_type"] == "browser_navigation_plan"
    assert action["params"]["target"]


def test_chat_navigation_when_browser_off_no_fake_session(monkeypatch):
    from aethos_core.api.main import app

    monkeypatch.setenv("BROWSER_AUTOMATION_ENABLED", "false")
    from aethos_core.config import get_settings

    get_settings.cache_clear()
    get_settings()
    client = TestClient(app)
    r = client.post(
        "/api/v1/chat",
        json={
            "message": "open vercel.com in browser automation",
            "session_id": "br-nav-off",
        },
    )
    body = r.json()
    assert r.status_code == 200
    reply = body["reply"].lower()
    assert "off" in reply or "disabled" in reply
    meta = body.get("meta") or {}
    assert meta.get("proposed_action_id", "") == ""
    get_settings.cache_clear()
    get_settings()


def test_chat_navigation_proposes_when_browser_enabled():
    from aethos_core.api.main import app

    use_mock_browser_driver(installed=True)
    try:
        client = TestClient(app)
        r = client.post(
            "/api/v1/chat",
            json={
                "message": "open vercel.com in browser automation",
                "session_id": "br-nav-on",
            },
        )
        body = r.json()
        assert r.status_code == 200
        meta = body.get("meta") or {}
        aid = meta.get("proposed_action_id", "")
        assert aid.startswith("act-")
        assert "approval" in body["reply"].lower()
    finally:
        reset_browser_test_state()
