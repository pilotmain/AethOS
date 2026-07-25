# SPDX-License-Identifier: Apache-2.0

from unittest.mock import patch

import pytest

from aethos_core.provider.completion import ProviderResult
from aethos_core.runtime.jobs import TrackedJob, JobStatus
from aethos_core.runtime.provider_job_runner import ProviderJobFailure, run_provider_job

from tests.job_test_utils import drain_job_executor


def test_empty_response_fails_job():
    prov = ProviderResult(
        text="Provider returned an empty response.",
        provider="anthropic",
        model="claude-sonnet-4-20250514",
        used_llm=True,
    )
    job = TrackedJob(
        id="job-empty",
        title="Empty",
        job_type="research_plan",
        status=JobStatus.QUEUED,
        source="chat",
        session_id="test",
        params={},
    )
    with (
        patch("aethos_core.runtime.provider_job_runner.provider_configured", return_value=True),
        patch("aethos_core.runtime.provider_job_runner._call_provider", return_value=prov),
    ):
        with pytest.raises(ProviderJobFailure) as exc:
            run_provider_job(job, timeout_sec=30)
    assert "empty" in exc.value.message.lower()


def test_empty_response_via_executor():
    from aethos_core.api.main import app
    from fastapi.testclient import TestClient

    prov = ProviderResult(
        text="Provider returned an empty response.",
        provider="anthropic",
        model="m",
        used_llm=True,
    )
    with (
        patch("aethos_core.runtime.provider_job_runner.provider_configured", return_value=True),
        patch("aethos_core.runtime.provider_job_runner._call_provider", return_value=prov),
    ):
        client = TestClient(app)
        created = client.post(
            "/api/v1/jobs",
            json={"title": "Empty", "job_type": "research_plan"},
        ).json()
        drain_job_executor()
        job = client.get(f"/api/v1/jobs/{created['id']}").json()["job"]
    assert job["status"] == "failed"
