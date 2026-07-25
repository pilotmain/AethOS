# SPDX-License-Identifier: Apache-2.0

import time
from unittest.mock import patch

import pytest

from aethos_core.runtime.jobs import TrackedJob, JobStatus
from aethos_core.runtime.provider_job_runner import ProviderJobTimeoutError, run_provider_job

from tests.job_test_utils import drain_job_executor


def test_provider_call_timeout_raises():
    def slow(_prompt: str):
        time.sleep(5)
        raise AssertionError("should not return")

    job = TrackedJob(
        id="job-timeout",
        title="Timeout",
        job_type="research_plan",
        status=JobStatus.QUEUED,
        source="chat",
        session_id="test",
        params={},
    )
    with (
        patch("aethos_core.runtime.provider_job_runner.provider_configured", return_value=True),
        patch("aethos_core.runtime.provider_job_runner._call_provider", side_effect=slow),
    ):
        with pytest.raises(ProviderJobTimeoutError):
            run_provider_job(job, timeout_sec=0.1)


def test_provider_timeout_finalizes_failed():
    from aethos_core.api.main import app
    from aethos_core.runtime.provider_job_runner import ProviderJobTimeoutError
    from fastapi.testclient import TestClient

    with patch(
        "aethos_core.runtime.job_executor.run_provider_job",
        side_effect=ProviderJobTimeoutError("Provider request timed out."),
    ):
        client = TestClient(app)
        created = client.post(
            "/api/v1/jobs",
            json={"title": "Timeout", "job_type": "research_plan"},
        ).json()
        drain_job_executor()
        job = client.get(f"/api/v1/jobs/{created['id']}").json()["job"]
    assert job["status"] == "failed"
    assert "timed out" in (job["failure_reason"] or "").lower()
