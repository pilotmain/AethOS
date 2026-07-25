# SPDX-License-Identifier: Apache-2.0

from fastapi.testclient import TestClient


def test_cancel_queued_job():
    from aethos_core.api.main import app

    client = TestClient(app)
    job = client.post(
        "/api/v1/jobs",
        json={
            "title": "Cancel me",
            "job_type": "manual_note",
            "auto_run": False,
        },
    ).json()
    assert job["status"] == "queued"
    cancelled = client.post(f"/api/v1/jobs/{job['id']}/cancel").json()
    assert cancelled["status"] == "cancelled"
    events = client.get(f"/api/v1/jobs/events?ids={job['id']}").json()["events"]
    types = [e["event_type"] for e in events]
    assert "job_cancelled" in types
    cancelled = [e for e in events if e["event_type"] == "job_cancelled"][0]
    assert "🚫" in cancelled["message"]


def test_cancel_running_job_rejected():
    from aethos_core.api.main import app

    client = TestClient(app)
    job = client.post(
        "/api/v1/jobs",
        json={"title": "Done fast", "job_type": "manual_note"},
    ).json()
    assert job["status"] == "completed"
    r = client.post(f"/api/v1/jobs/{job['id']}/cancel")
    assert r.status_code == 409
