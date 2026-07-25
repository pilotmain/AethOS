# SPDX-License-Identifier: Apache-2.0

import time
from unittest.mock import patch

from tests.job_test_utils import drain_job_executor


def test_provider_timeout_fails_job():
    from aethos_core.api.main import app
    from aethos_core.runtime.provider_job_runner import ProviderJobTimeoutError

    def slow_job(*_args, **_kwargs):
        time.sleep(2)
        raise AssertionError("should not complete")

    with patch(
        "aethos_core.runtime.job_executor.run_provider_job",
        side_effect=ProviderJobTimeoutError("Provider request timed out."),
    ):
        from fastapi.testclient import TestClient

        client = TestClient(app)
        created = client.post(
            "/api/v1/jobs",
            json={"title": "Timeout test", "job_type": "research_plan"},
        ).json()
        drain_job_executor()
        job = client.get(f"/api/v1/jobs/{created['id']}").json()["job"]
        assert job["status"] == "failed"
        assert "timed out" in (job["failure_reason"] or "").lower()
        events = client.get(f"/api/v1/jobs/events?ids={created['id']}").json()["events"]
        failed = [e for e in events if e["event_type"] == "job_failed"][0]
        assert "timed out" in failed["message"].lower()
