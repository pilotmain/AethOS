# SPDX-License-Identifier: Apache-2.0

from fastapi.testclient import TestClient


def test_deny_pending_action():
    from aethos_core.api.main import app

    client = TestClient(app)
    proposed = client.post(
        "/api/v1/actions/propose",
        json={"action_type": "vercel_cli_probe"},
    ).json()
    denied = client.post(f"/api/v1/actions/{proposed['id']}/deny")
    assert denied.status_code == 200
    assert denied.json()["status"] == "denied"


def test_denied_action_cannot_be_approved():
    from aethos_core.api.main import app

    client = TestClient(app)
    proposed = client.post(
        "/api/v1/actions/propose",
        json={"action_type": "terminal_probe"},
    ).json()
    client.post(f"/api/v1/actions/{proposed['id']}/deny")
    again = client.post("/api/v1/actions/approve", json={"action_id": proposed["id"]})
    assert again.status_code == 409


def test_deny_via_body_route():
    from aethos_core.api.main import app

    client = TestClient(app)
    proposed = client.post(
        "/api/v1/actions/propose",
        json={"action_type": "runtime_restart"},
    ).json()
    denied = client.post("/api/v1/actions/deny", json={"action_id": proposed["id"]})
    assert denied.status_code == 200
    assert denied.json()["status"] == "denied"


def test_actions_grouped_includes_denied():
    from aethos_core.api.main import app

    client = TestClient(app)
    proposed = client.post(
        "/api/v1/actions/propose",
        json={"action_type": "vercel_cli_probe"},
    ).json()
    client.post(f"/api/v1/actions/{proposed['id']}/deny")
    grouped = client.get("/api/v1/actions").json()["actions"]
    assert any(a["id"] == proposed["id"] for a in grouped["denied"])
