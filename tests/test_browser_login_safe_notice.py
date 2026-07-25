# SPDX-License-Identifier: Apache-2.0

from fastapi.testclient import TestClient


def test_login_dashboard_does_not_claim_access():
    from aethos_core.api.main import app

    client = TestClient(app)
    r = client.post(
        "/api/v1/chat",
        json={
            "message": "login to vercel.com and check my dashboard",
            "session_id": "br-login-1",
        },
    )
    body = r.json()
    reply = body["reply"].lower()
    assert r.status_code == 200
    assert "credential" in reply or "not store" in reply or "will not" in reply
    assert "logged into your account" not in reply
    assert "i logged" not in reply
    assert "enter your password" not in reply
    assert "provide your password" not in reply


def test_login_services_still_external_health_when_not_dashboard():
    from aethos_core.api.main import app

    from tests.job_test_utils import drain_job_executor

    client = TestClient(app)
    r = client.post(
        "/api/v1/chat",
        json={
            "message": "login to vercel.com and check my services",
            "session_id": "br-login-svc",
        },
    )
    body = r.json()
    jid = body["meta"].get("proposed_job_id", "")
    if jid:
        drain_job_executor()
        job = client.get(f"/api/v1/jobs/{jid}").json()["job"]
        assert job["job_type"] == "external_health_report"
    else:
        assert "browser" in body["reply"].lower() or "supervised" in body["reply"].lower()
