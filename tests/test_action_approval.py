# SPDX-License-Identifier: Apache-2.0

from fastapi.testclient import TestClient


def test_approve_vercel_cli_probe():
    from aethos_core.api.main import app

    client = TestClient(app)
    proposed = client.post(
        "/api/v1/actions/propose",
        json={"action_type": "vercel_cli_probe", "params": {}},
    ).json()
    approved = client.post(
        "/api/v1/actions/approve",
        json={"action_id": proposed["id"]},
    )
    assert approved.status_code == 200
    body = approved.json()
    assert body["status"] in ("completed", "failed")
    if body["status"] == "completed":
        assert body["result"]


def test_double_approve_rejected():
    from aethos_core.api.main import app

    client = TestClient(app)
    proposed = client.post(
        "/api/v1/actions/propose",
        json={"action_type": "runtime_restart", "params": {}},
    ).json()
    assert client.post("/api/v1/actions/approve", json={"action_id": proposed["id"]}).status_code == 200
    again = client.post("/api/v1/actions/approve", json={"action_id": proposed["id"]})
    assert again.status_code == 409
