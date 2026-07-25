# SPDX-License-Identifier: Apache-2.0

from fastapi.testclient import TestClient


def test_job_lifecycle_events_emitted():
    from aethos_core.api.main import app

    client = TestClient(app)
    job = client.post(
        "/api/v1/jobs",
        json={"title": "Checklist", "job_type": "checklist_generation"},
    ).json()  # local — sync complete
    jid = job["id"]
    events = client.get(f"/api/v1/jobs/events?ids={jid}").json()["events"]
    types = [e["event_type"] for e in events]
    assert "job_created" in types
    assert "job_started" in types
    assert "job_completed" in types
    assert all(e["message"] for e in events)
    assert all(e["job_id"] == jid for e in events)


def test_job_events_ordered_unique():
    from unittest.mock import patch

    from aethos_core.api.main import app
    from tests.job_test_utils import drain_job_executor, mock_provider_job_result

    mock_result = mock_provider_job_result("plan", job_type="research_plan", title="Plan")
    with patch(
        "aethos_core.runtime.job_executor.run_provider_job",
        return_value=mock_result,
    ):
        client = TestClient(app)
        job = client.post(
            "/api/v1/jobs",
            json={"title": "Plan", "job_type": "research_plan"},
        ).json()
        drain_job_executor()
        events = client.get(f"/api/v1/jobs/events?ids={job['id']}").json()["events"]
        ids = [e["id"] for e in events]
        assert len(ids) == len(set(ids))
        assert events[0]["at"] <= events[-1]["at"]
