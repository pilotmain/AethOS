# SPDX-License-Identifier: Apache-2.0

from fastapi.testclient import TestClient


def test_runtime_restart_contract():
    from aethos_core.api.main import app

    client = TestClient(app)
    proposed = client.post(
        "/api/v1/actions/propose",
        json={"action_type": "runtime_restart"},
    ).json()
    assert proposed["status"] == "pending"
    approved = client.post("/api/v1/actions/approve", json={"action_id": proposed["id"]})
    body = approved.json()
    assert body["status"] == "completed"
    assert "restart" in (body.get("result") or "").lower()
    assert "8010" in body["result"]


def test_list_actions_grouped():
    from aethos_core.api.main import app

    client = TestClient(app)
    client.post("/api/v1/actions/propose", json={"action_type": "runtime_restart"})
    listing = client.get("/api/v1/actions")
    assert listing.status_code == 200
    data = listing.json()
    assert "pending" in data["actions"]
    assert data["count"] >= 1
