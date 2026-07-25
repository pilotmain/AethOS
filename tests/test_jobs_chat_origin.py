# SPDX-License-Identifier: Apache-2.0

from fastapi.testclient import TestClient


def test_chat_creates_tracked_job():
    from aethos_core.api.main import app

    client = TestClient(app)
    r = client.post(
        "/api/v1/chat",
        json={
            "message": "make a tracked task to draft an AethOS MVP checklist",
            "session_id": "job-chat-1",
        },
    )
    body = r.json()
    assert body["meta"]["proposed_job_id"].startswith("job-")
    assert body.get("job") and body["job"]["id"].startswith("job-")
    assert "Created tracked job" in body["reply"]


def test_chat_checklist_job_completes_with_events():
    from aethos_core.api.main import app

    client = TestClient(app)
    r = client.post(
        "/api/v1/chat",
        json={
            "message": "create a checklist for AethOS next steps",
            "session_id": "job-chat-2",
        },
    )
    jid = r.json()["meta"]["proposed_job_id"]
    events = client.get(f"/api/v1/jobs/events?ids={jid}").json()["events"]
    assert "job_completed" in [e["event_type"] for e in events]
    completed = [e for e in events if e["event_type"] == "job_completed"][0]
    assert "✅" in completed["message"]


def test_chat_job_status_handler():
    from aethos_core.api.main import app

    client = TestClient(app)
    created = client.post(
        "/api/v1/jobs",
        json={"title": "Status test", "job_type": "manual_note"},
    ).json()
    jid = created["id"]
    r = client.post(
        "/api/v1/chat",
        json={"message": f"status of {jid}", "session_id": "job-chat-3"},
    )
    assert jid in r.json()["reply"]
    assert "completed" in r.json()["reply"].lower()
