# SPDX-License-Identifier: Apache-2.0

from unittest.mock import patch

from fastapi.testclient import TestClient


def test_jobs_events_transient_failure_does_not_change_job_status():
    from aethos_core.api.main import app
    from aethos_core.runtime.authority import authority
    from aethos_core.runtime.jobs import job_store

    job = authority.create_job(
        title="Checklist",
        job_type="checklist_generation",
        params={"topic": "test"},
        source="test",
        session_id="transient",
        auto_run=False,
    )
    job_store.complete_with_result(
        job.id,
        full_result="# Checklist",
        summary="Checklist ready",
        preview="# Checklist",
        provider="local",
        model="template",
        used_llm=False,
        fallback=False,
    )

    client = TestClient(app)
    with patch(
        "aethos_core.api.routes.jobs.authority.list_job_events",
        side_effect=RuntimeError("temporary"),
    ):
        r = client.get(f"/api/v1/jobs/events?ids={job.id}")
    assert r.status_code == 200
    assert r.json()["ok"] is False

    stored = job_store.get(job.id)
    assert stored is not None
    assert stored.status.value == "completed"

    r2 = client.get(f"/api/v1/jobs/{job.id}")
    assert r2.status_code == 200
    assert r2.json()["job"]["status"] == "completed"
