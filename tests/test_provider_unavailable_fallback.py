# SPDX-License-Identifier: Apache-2.0

from unittest.mock import patch

from fastapi.testclient import TestClient

from tests.job_test_utils import drain_job_executor


def test_provider_unavailable_uses_fallback():
    from aethos_core.api.main import app

    with patch("aethos_core.runtime.provider_job_runner.provider_configured", return_value=False):
        client = TestClient(app)
        r = client.post(
            "/api/v1/chat",
            json={"message": "generate an MVP roadmap", "session_id": "fallback-1"},
        )
        jid = r.json()["meta"]["proposed_job_id"]
        drain_job_executor()
        job = client.get(f"/api/v1/jobs/{jid}").json()["job"]
        assert job["status"] == "completed"
        assert "Provider unavailable" in (job["result"] or "")
        assert job["params"].get("provider_fallback") is True
