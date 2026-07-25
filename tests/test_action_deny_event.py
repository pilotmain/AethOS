# SPDX-License-Identifier: Apache-2.0

from fastapi.testclient import TestClient


def test_deny_emits_action_denied_event():
    from aethos_core.api.main import app

    client = TestClient(app)
    proposed = client.post(
        "/api/v1/actions/propose",
        json={"action_type": "vercel_cli_probe", "source": "chat"},
    ).json()
    aid = proposed["id"]
    client.post(f"/api/v1/actions/{aid}/deny")
    events = client.get(f"/api/v1/actions/events?ids={aid}").json()["events"]
    denied = [e for e in events if e["event_type"] == "action_denied"]
    assert len(denied) == 1
    assert "🚫" in denied[0]["message"]
    assert "Vercel CLI probe was not run" in denied[0]["message"]
