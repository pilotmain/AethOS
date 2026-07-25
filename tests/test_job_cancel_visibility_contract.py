# SPDX-License-Identifier: Apache-2.0

from fastapi.testclient import TestClient


def test_queued_job_listed_under_grouped_queued():
    from aethos_core.api.main import app

    client = TestClient(app)
    job = client.post(
        "/api/v1/jobs",
        json={"title": "Cancel visibility test", "job_type": "manual_note", "auto_run": False},
    ).json()
    grouped = client.get("/api/v1/jobs").json()["grouped"]
    assert any(j["id"] == job["id"] for j in grouped["queued"])


def test_completed_job_not_in_queued():
    from aethos_core.api.main import app

    client = TestClient(app)
    job = client.post(
        "/api/v1/jobs",
        json={"title": "Fast complete", "job_type": "manual_note"},
    ).json()
    assert job["status"] == "completed"
    grouped = client.get("/api/v1/jobs").json()["grouped"]
    assert not any(j["id"] == job["id"] for j in grouped["queued"])
