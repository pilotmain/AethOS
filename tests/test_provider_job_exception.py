# SPDX-License-Identifier: Apache-2.0

from unittest.mock import patch

import pytest

from aethos_core.runtime.jobs import TrackedJob, JobStatus
from aethos_core.runtime.provider_job_runner import ProviderJobFailure, run_provider_job

from tests.job_test_utils import drain_job_executor


def test_provider_exception_raises_failure():
    job = TrackedJob(
        id="job-exc",
        title="Exc",
        job_type="research_plan",
        status=JobStatus.QUEUED,
        source="chat",
        session_id="test",
        params={},
    )
    with (
        patch("aethos_core.runtime.provider_job_runner.provider_configured", return_value=True),
        patch(
            "aethos_core.runtime.provider_job_runner._call_provider",
            side_effect=RuntimeError("network down"),
        ),
    ):
        with pytest.raises(ProviderJobFailure) as exc:
            run_provider_job(job, timeout_sec=30)
    assert "network down" in exc.value.message


def test_provider_exception_finalizes_job():
    from aethos_core.api.main import app
    from fastapi.testclient import TestClient

    with (
        patch("aethos_core.runtime.provider_job_runner.provider_configured", return_value=True),
        patch(
            "aethos_core.runtime.provider_job_runner._call_provider",
            side_effect=ValueError("sdk exploded"),
        ),
    ):
        client = TestClient(app)
        created = client.post(
            "/api/v1/jobs",
            json={"title": "Exc", "job_type": "research_plan"},
        ).json()
        drain_job_executor()
        job = client.get(f"/api/v1/jobs/{created['id']}").json()["job"]
    assert job["status"] == "failed"
    assert "sdk exploded" in (job["failure_reason"] or "")
