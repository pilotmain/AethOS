# SPDX-License-Identifier: Apache-2.0

from fastapi.testclient import TestClient


def test_action_lifecycle_events_on_approve():
    from aethos_core.api.main import app

    client = TestClient(app)
    proposed = client.post(
        "/api/v1/actions/propose",
        json={"action_type": "vercel_cli_probe", "params": {}, "source": "chat"},
    ).json()
    aid = proposed["id"]
    client.post("/api/v1/actions/approve", json={"action_id": aid})

    events = client.get(f"/api/v1/actions/events?ids={aid}").json()["events"]
    types = [e["event_type"] for e in events]
    assert "action_approved" in types
    assert types[-1] in ("action_completed", "action_failed")
    assert all(e["message"] for e in events)


def test_events_ordered_and_deduped_by_id():
    from aethos_core.api.main import app

    client = TestClient(app)
    proposed = client.post(
        "/api/v1/actions/propose",
        json={"action_type": "runtime_restart"},
    ).json()
    aid = proposed["id"]
    client.post("/api/v1/actions/approve", json={"action_id": aid})
    events = client.get(f"/api/v1/actions/events?ids={aid}").json()["events"]
    assert len(events) >= 2
    ids = [e["id"] for e in events]
    assert len(ids) == len(set(ids))
    assert events[0]["at"] <= events[-1]["at"]


def test_chat_proposal_includes_action_meta():
    from aethos_core.api.main import app

    client = TestClient(app)
    r = client.post(
        "/api/v1/chat",
        json={"message": "can you check Vercel CLI?", "session_id": "lifecycle1"},
    )
    body = r.json()
    assert body["meta"] and body["meta"].get("proposed_action_id", "").startswith("act-")
    assert body.get("action") and body["action"]["id"].startswith("act-")
    assert body["action"].get("lifecycle_tracked") is True


def test_chat_action_status_handler():
    from aethos_core.api.main import app

    client = TestClient(app)
    proposed = client.post(
        "/api/v1/actions/propose",
        json={"action_type": "vercel_cli_probe"},
    ).json()
    aid = proposed["id"]
    client.post("/api/v1/actions/approve", json={"action_id": aid})
    r = client.post(
        "/api/v1/chat",
        json={"message": f"what happened to {aid}?", "session_id": "status1"},
    )
    body = r.json()
    assert aid in body["reply"]
    assert "completed" in body["reply"].lower() or "failed" in body["reply"].lower()


def test_action_status_endpoint():
    from aethos_core.api.main import app

    client = TestClient(app)
    proposed = client.post(
        "/api/v1/actions/propose",
        json={"action_type": "terminal_probe"},
    ).json()
    st = client.get(f"/api/v1/actions/{proposed['id']}/status")
    assert st.status_code == 200
    assert st.json()["action"]["id"] == proposed["id"]
