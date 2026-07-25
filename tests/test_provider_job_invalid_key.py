# SPDX-License-Identifier: Apache-2.0

from unittest.mock import patch

import pytest

from aethos_core.provider.completion import ProviderResult
from aethos_core.runtime.jobs import TrackedJob, JobStatus
from aethos_core.runtime.provider_job_runner import ProviderJobFailure, run_provider_job

from tests.job_test_utils import drain_job_executor


def _job() -> TrackedJob:
    return TrackedJob(
        id="job-bad-key",
        title="Research",
        job_type="research_plan",
        status=JobStatus.QUEUED,
        source="chat",
        session_id="test",
        params={"topic": "test"},
    )


def test_invalid_key_raises_provider_job_failure():
    prov = ProviderResult(
        text="Provider request failed: Client error '401 Unauthorized'",
        provider="anthropic",
        model="claude-sonnet-4-20250514",
        used_llm=False,
    )
    with (
        patch("aethos_core.runtime.provider_job_runner.provider_configured", return_value=True),
        patch("aethos_core.runtime.provider_job_runner._call_provider", return_value=prov),
    ):
        with pytest.raises(ProviderJobFailure) as exc:
            run_provider_job(_job(), timeout_sec=30)
    assert "Invalid Anthropic API key" in exc.value.message


def test_invalid_key_finalizes_job_as_failed():
    from aethos_core.api.main import app
    from fastapi.testclient import TestClient

    prov = ProviderResult(
        text="Provider request failed: 401",
        provider="anthropic",
        model="m",
        used_llm=False,
    )
    with (
        patch("aethos_core.runtime.provider_job_runner.provider_configured", return_value=True),
        patch("aethos_core.runtime.provider_job_runner._call_provider", return_value=prov),
    ):
        client = TestClient(app)
        created = client.post(
            "/api/v1/jobs",
            json={"title": "Bad key", "job_type": "research_plan"},
        ).json()
        drain_job_executor()
        job = client.get(f"/api/v1/jobs/{created['id']}").json()["job"]
    assert job["status"] == "failed"
    assert "key" in (job["failure_reason"] or "").lower()
