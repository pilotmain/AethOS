# SPDX-License-Identifier: Apache-2.0

VERCEL_PROMPT = (
    "please login to vercel.com and give me a report of all the services health?"
)


def test_health_endpoint():
    from fastapi.testclient import TestClient

    from aethos_core.api.main import app

    client = TestClient(app)
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    body = r.json()
    assert body["chat_ready"] is True
    assert "capabilities" in body


def test_vercel_prompt_deterministic_terminal():
    from fastapi.testclient import TestClient

    from aethos_core.api.main import app

    client = TestClient(app)
    r = client.post(
        "/api/v1/chat/deterministic",
        json={"message": VERCEL_PROMPT, "session_id": "default"},
    )
    assert r.status_code == 200
    body = r.json()
    assert isinstance(body["reply"], str)
    assert body["reply"].strip()
    assert body["terminal"] is True
    assert body["provider_stream"] is False
    assert "vercel" in body["reply"].lower()


def test_panel_state_does_not_block_chat():
    from aethos_core.runtime.authority import PanelState, authority

    authority.record_panel_state(PanelState.DEGRADED)
    snap = authority.snapshot()
    assert snap.chat_ready is True
    assert "panel" in snap.label.lower() or snap.panel.value == "degraded"
