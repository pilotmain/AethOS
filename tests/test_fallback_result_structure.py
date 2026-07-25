# SPDX-License-Identifier: Apache-2.0

from aethos_core.runtime.jobs import TrackedJob, JobStatus
from aethos_core.runtime.provider_job_runner import fallback_result


def test_fallback_result_matches_artifact_shape():
    job = TrackedJob(
        id="job-fb",
        title="Roadmap",
        job_type="roadmap_generation",
        status=JobStatus.QUEUED,
        source="test",
        session_id="s",
        params={"user_request": "mvp roadmap"},
    )
    out = fallback_result(job)
    assert out.fallback is True
    assert out.provider == "none"
    assert out.model == "template"
    assert out.full_result
    assert out.summary
    assert out.preview
    assert "⚠️" in out.full_result
    assert out.text == out.full_result
    assert len(out.summary) < len(out.full_result)
