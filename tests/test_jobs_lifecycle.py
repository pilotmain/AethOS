# SPDX-License-Identifier: Apache-2.0

from fastapi.testclient import TestClient


def test_job_create_and_complete():
    from aethos_core.api.main import app

    client = TestClient(app)
    job = client.post(
        "/api/v1/jobs",
        json={
            "title": "Draft MVP checklist",
            "job_type": "checklist_generation",
            "source": "chat",
            "params": {"topic": "AethOS MVP"},
        },
    ).json()
    assert job["id"].startswith("job-")
    assert job["status"] == "completed"  # local jobs finish synchronously
    assert job["result"]
    assert job["title"] == "Draft MVP checklist"


def test_job_has_required_fields():
    from aethos_core.api.main import app

    client = TestClient(app)
    job = client.post(
        "/api/v1/jobs",
        json={"title": "Note", "job_type": "manual_note"},
    ).json()
    for key in (
        "id",
        "title",
        "status",
        "created_at",
        "updated_at",
        "source",
        "job_type",
    ):
        assert key in job


def test_list_jobs_grouped():
    from aethos_core.api.main import app

    client = TestClient(app)
    client.post(
        "/api/v1/jobs",
        json={"title": "One", "job_type": "manual_note"},
    )
    body = client.get("/api/v1/jobs").json()
    assert "jobs" in body
    assert "grouped" in body
    assert "completed" in body["grouped"]
    assert body["count"] >= 1


def test_get_job_by_id():
    from aethos_core.api.main import app
    from unittest.mock import patch

    from tests.job_test_utils import drain_job_executor, mock_provider_job_result

    mock_result = mock_provider_job_result("research ok", job_type="research_plan", title="Research")
    with patch(
        "aethos_core.runtime.job_executor.run_provider_job",
        return_value=mock_result,
    ):
        client = TestClient(app)
        created = client.post(
            "/api/v1/jobs",
            json={"title": "Research", "job_type": "research_plan"},
        ).json()
        drain_job_executor()
        detail = client.get(f"/api/v1/jobs/{created['id']}").json()
        assert detail["job"]["id"] == created["id"]
        assert len(detail["events"]) >= 2
