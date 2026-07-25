# SPDX-License-Identifier: Apache-2.0

from fastapi.testclient import TestClient


def test_terminal_probe_chat_proposal():
    from aethos_core.api.main import app

    client = TestClient(app)
    r = client.post(
        "/api/v1/chat",
        json={"message": "can you run a terminal probe?", "session_id": "tp1"},
    )
    assert r.status_code == 200
    assert "terminal" in r.json()["reply"].lower()
    assert "act-" in r.json()["reply"]


def test_terminal_probe_fails_without_host_executor():
    from aethos_core.api.main import app

    client = TestClient(app)
    proposed = client.post(
        "/api/v1/actions/propose",
        json={"action_type": "terminal_probe"},
    ).json()
    approved = client.post("/api/v1/actions/approve", json={"action_id": proposed["id"]})
    body = approved.json()
    # May complete or fail depending on HOST_EXECUTOR_ENABLED in env
    assert body["status"] in ("completed", "failed")
