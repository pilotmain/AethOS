# SPDX-License-Identifier: Apache-2.0

from fastapi.testclient import TestClient


def test_propose_action():
    from aethos_core.api.main import app

    client = TestClient(app)
    r = client.post(
        "/api/v1/actions/propose",
        json={"action_type": "terminal_probe", "params": {}, "source": "test"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "pending"
    assert body["action_type"] == "terminal_probe"
    assert body["id"].startswith("act-")


def test_propose_unknown_action_rejected():
    from aethos_core.api.main import app

    client = TestClient(app)
    r = client.post(
        "/api/v1/actions/propose",
        json={"action_type": "dangerous_shell", "params": {}},
    )
    assert r.status_code == 422


def test_chat_restart_proposes_action():
    from aethos_core.api.main import app

    client = TestClient(app)
    r = client.post(
        "/api/v1/chat",
        json={"message": "can you restart AethOS?", "session_id": "act1"},
    )
    assert r.status_code == 200
    reply = r.json()["reply"]
    assert "propose" in reply.lower() or "approval" in reply.lower()
    assert "act-" in reply
    assert "Mission Control" in reply
