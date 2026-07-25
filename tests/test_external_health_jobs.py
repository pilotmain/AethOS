# SPDX-License-Identifier: Apache-2.0

from unittest.mock import patch

from fastapi.testclient import TestClient

from tests.job_test_utils import drain_job_executor


def test_vercel_health_prompt_creates_tracked_job():
    from aethos_core.api.main import app

    client = TestClient(app)
    r = client.post(
        "/api/v1/chat",
        json={"message": "check Vercel service health", "session_id": "ext-health-1"},
    )
    body = r.json()
    assert r.status_code == 200
    assert body["terminal"] is True
    assert "Created tracked job" in body["reply"]
    assert "Mission Control" in body["reply"]
    jid = body["meta"]["proposed_job_id"]
    assert jid.startswith("job-")
    drain_job_executor()
    job = client.get(f"/api/v1/jobs/{jid}").json()["job"]
    assert job["status"] == "completed"
    assert job["job_type"] == "external_health_report"
    assert job.get("result_summary")
    assert "Vercel" in (job.get("full_result") or job.get("result") or "")


def test_external_job_lifecycle_events_are_summary_safe():
    from aethos_core.api.main import app

    client = TestClient(app)
    created = client.post(
        "/api/v1/chat",
        json={"message": "give me a Vercel health report", "session_id": "ext-health-2"},
    ).json()
    jid = created["meta"]["proposed_job_id"]
    drain_job_executor()
    events = client.get(f"/api/v1/jobs/events?ids={jid}").json()["events"]
    completed = [e for e in events if e["event_type"] == "job_completed"][0]
    assert "Summary:" in completed["message"]
    assert "Mission Control" in completed["message"]
    full = client.get(f"/api/v1/jobs/{jid}").json()["job"].get("full_result") or ""
    if len(full) > 400:
        assert full not in completed["message"]
