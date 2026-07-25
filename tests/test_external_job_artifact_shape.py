# SPDX-License-Identifier: Apache-2.0

from aethos_core.runtime.external_jobs import run_external_health_job
from aethos_core.runtime.jobs import TrackedJob, JobStatus


def test_external_job_result_artifact_shape():
    job = TrackedJob(
        id="job-ext-art",
        title="Vercel health",
        job_type="external_health_report",
        status=JobStatus.QUEUED,
        source="test",
        session_id="s",
        params={
            "target": "vercel",
            "mode": "public",
            "user_request": "check Vercel service health",
        },
    )
    out = run_external_health_job(job)
    assert out.full_result
    assert out.summary
    assert out.preview
    assert out.summary != out.full_result
    assert out.provider == "none"
    assert out.tool_used == "external_health_report"
    assert out.sources
    assert out.used_llm is False
