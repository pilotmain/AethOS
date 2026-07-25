# SPDX-License-Identifier: Apache-2.0

from unittest.mock import patch

from fastapi.testclient import TestClient


def test_jobs_events_error_boundary_returns_structured_empty():
    from aethos_core.api.main import app

    client = TestClient(app)
    with patch(
        "aethos_core.api.routes.jobs.authority.list_job_events",
        side_effect=RuntimeError("event store blew up"),
    ):
        r = client.get("/api/v1/jobs/events?ids=job-abc")
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is False
    assert body["events"] == []
    assert body["error"]["code"] == "EVENT_POLL_FAILED"
    assert "event store blew up" in body["error"]["detail"]
