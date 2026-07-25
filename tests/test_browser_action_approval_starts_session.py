# SPDX-License-Identifier: Apache-2.0

from fastapi.testclient import TestClient

from tests.browser_test_utils import reset_browser_test_state, use_mock_browser_driver


def test_chat_approve_opens_session_lifecycle():
    from aethos_core.api.main import app
    mock = use_mock_browser_driver(installed=True)
    try:
        client = TestClient(app)
        chat = client.post(
            "/api/v1/chat",
            json={
                "message": "open vercel.com in browser automation",
                "session_id": "p8-chat",
            },
        ).json()
        aid = (chat.get("meta") or {}).get("proposed_action_id", "")
        assert aid.startswith("act-")
        from tests.browser_test_utils import drain_browser_executor

        client.post(f"/api/v1/actions/{aid}/approve")
        drain_browser_executor()
        approved = client.get(f"/api/v1/actions/{aid}/status").json()["action"]
        assert approved["status"] == "completed"
        events = client.get(f"/api/v1/actions/events?ids={aid}").json()["events"]
        msgs = [e["message"] for e in events]
        assert any("browser session launching" in m.lower() for m in msgs)
        assert any("browser session opened" in m.lower() for m in msgs)
        assert mock.opened_urls
    finally:
        reset_browser_test_state()
