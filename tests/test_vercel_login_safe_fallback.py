# SPDX-License-Identifier: Apache-2.0

from fastapi.testclient import TestClient

from tests.job_test_utils import drain_job_executor


def test_login_dashboard_request_does_not_claim_access():
    from aethos_core.api.main import app

    client = TestClient(app)
    r = client.post(
        "/api/v1/chat",
        json={
            "message": "login to vercel.com and check my services",
            "session_id": "ext-login-1",
        },
    )
    body = r.json()
    reply = body["reply"]
    assert r.status_code == 200
    low = reply.lower()
    assert (
        "not enabled" in low
        or "not supported" in low
        or "browser session" in low
        or "supervised" in low
    )
    assert "not store credentials" in low or "will **not** store" in reply.lower()
    meta = body.get("meta") or {}
    jid = meta.get("proposed_job_id")
    if jid:
        drain_job_executor()
        job = client.get(f"/api/v1/jobs/{jid}").json()["job"]
        assert job["job_type"] in ("browser_session", "external_health_report")


def test_cli_status_still_proposes_approval_action():
    from aethos_core.api.main import app

    client = TestClient(app)
    r = client.post(
        "/api/v1/chat",
        json={"message": "check Vercel CLI status", "session_id": "ext-cli-1"},
    )
    body = r.json()
    assert body["meta"].get("proposed_action_id", "").startswith("act-")
    assert "Approve" in body["reply"] or "Mission Control" in body["reply"]
