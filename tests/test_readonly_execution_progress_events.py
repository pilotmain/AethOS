# SPDX-License-Identifier: Apache-2.0

from aethos_core.runtime.jobs import job_store


def test_readonly_execution_progress_updates_timeline():
    job_store.clear_for_tests()
    try:
        job = job_store.create(
            title="Read-only execution",
            job_type="readonly_execution_vercel",
            params={},
            auto_run=False,
        )
        job_store.begin_running(job.id)
        job_store.emit_progress(job.id, "Fetching deployments")
        running = job_store.get(job.id)
        assert running is not None
        timeline = running.params.get("execution_timeline")
        assert isinstance(timeline, list)
        assert any("Fetching deployments" in str(e.get("message", "")) for e in timeline if isinstance(e, dict))
        assert running.params.get("last_progress_at")
    finally:
        job_store.clear_for_tests()
