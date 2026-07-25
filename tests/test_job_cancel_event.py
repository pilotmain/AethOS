# SPDX-License-Identifier: Apache-2.0

from fastapi.testclient import TestClient


def test_cancel_emits_job_cancelled_with_chat_message():
    from aethos_core.api.main import app

    client = TestClient(app)
    job = client.post(
        "/api/v1/jobs",
        json={
            "title": "test cancel",
            "job_type": "manual_note",
            "source": "chat",
            "auto_run": False,
        },
    ).json()
    jid = job["id"]
    client.post(f"/api/v1/jobs/{jid}/cancel")
    events = client.get(f"/api/v1/jobs/events?ids={jid}").json()["events"]
    cancelled = [e for e in events if e["event_type"] == "job_cancelled"]
    assert len(cancelled) == 1
    assert "🚫" in cancelled[0]["message"]
    assert "test cancel" in cancelled[0]["message"]


def test_chat_queued_tracked_task_for_cancel_test():
    from aethos_core.api.main import app

    client = TestClient(app)
    r = client.post(
        "/api/v1/chat",
        json={
            "message": "make a queued tracked task to test cancel",
            "session_id": "cancel-chat-1",
        },
    )
    body = r.json()
    jid = body["meta"]["proposed_job_id"]
    job = client.get(f"/api/v1/jobs/{jid}").json()["job"]
    assert job["status"] == "queued"
