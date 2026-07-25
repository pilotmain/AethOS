# SPDX-License-Identifier: Apache-2.0

from unittest.mock import patch

from aethos_core.provider.completion import ProviderResult
from aethos_core.runtime.jobs import TrackedJob, JobStatus
from aethos_core.runtime.provider_job_runner import run_provider_job

from tests.job_test_utils import drain_job_executor


def _sample_job() -> TrackedJob:
    return TrackedJob(
        id="job-test-success",
        title="research the top competitors to AethOS",
        job_type="comparison_brief",
        status=JobStatus.QUEUED,
        source="chat",
        session_id="test",
        params={"user_request": "research the top competitors to AethOS"},
    )


def test_provider_job_success_returns_real_llm_output():
    prov = ProviderResult(
        text="# Competitors\n\n- LangGraph — orchestration\n- CrewAI — multi-agent",
        provider="anthropic",
        model="claude-sonnet-4-20250514",
        used_llm=True,
    )
    with (
        patch("aethos_core.runtime.provider_job_runner.provider_configured", return_value=True),
        patch("aethos_core.runtime.provider_job_runner._call_provider", return_value=prov),
    ):
        out = run_provider_job(_sample_job(), timeout_sec=30)
    assert out.fallback is False
    assert out.provider == "anthropic"
    assert "LangGraph" in out.text
    assert "Provider unavailable" not in out.text


def test_provider_job_success_via_executor():
    from aethos_core.api.main import app
    from fastapi.testclient import TestClient

    prov = ProviderResult(
        text="## Competitor brief\n\nMeaningful analysis from the model.",
        provider="anthropic",
        model="claude-sonnet-4-20250514",
        used_llm=True,
    )
    with (
        patch("aethos_core.runtime.provider_job_runner.provider_configured", return_value=True),
        patch("aethos_core.runtime.provider_job_runner._call_provider", return_value=prov),
    ):
        client = TestClient(app)
        created = client.post(
            "/api/v1/jobs",
            json={
                "title": "Competitors",
                "job_type": "comparison_brief",
                "params": {"user_request": "research competitors"},
            },
        ).json()
        drain_job_executor()
        job = client.get(f"/api/v1/jobs/{created['id']}").json()["job"]
    assert job["status"] == "completed"
    assert job["provider_used"] == "anthropic"
    assert job["params"].get("provider_fallback") is False
    assert "Meaningful" in (job["result"] or "")
