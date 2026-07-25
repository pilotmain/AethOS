# SPDX-License-Identifier: Apache-2.0

from fastapi.testclient import TestClient


def test_jobs_events_blocked_preflight_metadata_serializes():
    from aethos_core.api.main import app
    from aethos_core.runtime.authority import authority
    from aethos_core.runtime.jobs import job_store

    job = authority.create_job(
        title="Logs preflight",
        job_type="vercel_logs_preflight",
        params={
            "user_request": "check logs for talking-avatar-agent",
            "preflight_status": "blocked",
            "operation_preflight": {
                "provider": "vercel",
                "operation_type": "check_logs",
                "target_name": "talking-avatar-agent",
                "target_status": "blocked_by_browser_runtime",
                "preflight_status": "blocked",
                "blockers": ["Browser runtime is not ready"],
            },
        },
        source="test",
        session_id="blocked-pf",
        auto_run=False,
    )
    job_store.complete_with_result(
        job.id,
        full_result="Preflight complete",
        summary="Latest Vercel inventory is unavailable.",
        preview="Preflight complete",
        provider="preflight",
        model="deterministic",
        used_llm=False,
        fallback=False,
    )

    client = TestClient(app)
    r = client.get(f"/api/v1/jobs/events?ids={job.id}")
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["count"] >= 1
    completed = [e for e in body["events"] if e["event_type"] == "job_completed"]
    assert completed
    assert "blocked" in completed[-1]["message"].lower() or "inventory" in completed[-1]["message"].lower()

    stored = job_store.get(job.id)
    assert stored is not None
    assert stored.status.value == "completed"
