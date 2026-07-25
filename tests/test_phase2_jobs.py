# SPDX-License-Identifier: Apache-2.0

from fastapi.testclient import TestClient


def test_jobs_endpoint():
    from aethos_core.api.main import app

    client = TestClient(app)
    r = client.get("/api/v1/jobs")
    assert r.status_code == 200
    body = r.json()
    assert "jobs" in body
    assert "grouped" in body
    assert "queued" in body["grouped"]
    assert isinstance(body["count"], int)


def test_actions_endpoint_still_grouped():
    from aethos_core.api.main import app

    client = TestClient(app)
    r = client.get("/api/v1/actions")
    assert r.status_code == 200
    body = r.json()
    assert "actions" in body
    assert "pending" in body["actions"]
