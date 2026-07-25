# SPDX-License-Identifier: Apache-2.0

import pytest

from aethos_core.operations.operation_models import OperationPreflight
from aethos_core.operations.preflight_execution import (
    PreflightExecutionError,
    validate_preflight_job,
)
from aethos_core.runtime.jobs import JobStatus, TrackedJob, job_store


@pytest.fixture
def job_env(tmp_path, monkeypatch):
    monkeypatch.setenv("BROWSER_PROFILES_DIR", str(tmp_path / "browser_profiles"))
    job_store._jobs.clear()
    yield
    job_store._jobs.clear()


def _completed_preflight(**pf_overrides):
    pf = OperationPreflight(
        provider="local",
        operation_type="local_workspace_fix",
        target_name="/tmp/ws",
        target_status="resolved",
        preflight_status="ready_for_approval",
    )
    data = pf.to_dict()
    data.update(pf_overrides)
    job = TrackedJob(
        id="job-pf-test",
        title="Local preflight",
        job_type="local_workspace_fix_preflight",
        status=JobStatus.COMPLETED,
        source="chat",
        session_id="test",
        params={
            "operation_preflight": data,
            "preflight_status": data.get("preflight_status"),
            "is_current": True,
        },
    )
    job_store._jobs[job.id] = job
    return job


def test_completed_preflight_can_validate(job_env):
    job = _completed_preflight()
    params = validate_preflight_job(job)
    assert "git_status" in params["approved_actions"]


def test_needs_information_blocked(job_env):
    job = _completed_preflight(preflight_status="needs_information", missing_information=["x"])
    job.params["preflight_status"] = "needs_information"
    with pytest.raises(PreflightExecutionError):
        validate_preflight_job(job)


def test_mutating_operation_blocked(job_env):
    job = _completed_preflight()
    job.job_type = "vercel_redeploy_preflight"
    pf = job.params["operation_preflight"]
    pf["operation_type"] = "redeploy"
    pf["provider"] = "vercel"
    with pytest.raises(PreflightExecutionError):
        validate_preflight_job(job)
