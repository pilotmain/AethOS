# SPDX-License-Identifier: Apache-2.0

import pytest

from aethos_core.runtime.jobs import JobStatus, TrackedJob, job_store


@pytest.fixture
def job_env(tmp_path, monkeypatch):
    monkeypatch.setenv("BROWSER_PROFILES_DIR", str(tmp_path / "browser_profiles"))
    job_store._jobs.clear()
    yield
    job_store._jobs.clear()


def test_cancel_queued_execution_job(job_env):
    job = TrackedJob(
        id="job-exec-q",
        title="Queued execution",
        job_type="readonly_execution_local",
        status=JobStatus.QUEUED,
        source="chat",
        session_id="test",
        params={"read_only": True},
    )
    job_store._jobs[job.id] = job
    cancelled = job_store.cancel(job.id)
    assert cancelled.status == JobStatus.CANCELLED
