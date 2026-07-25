# SPDX-License-Identifier: Apache-2.0

from aethos_core.runtime.jobs import job_store


def test_readonly_execution_last_progress_updates_on_each_step():
    job_store.clear_for_tests()
    try:
        job = job_store.create(
            title="Read-only execution",
            job_type="readonly_execution_vercel",
            params={},
            auto_run=False,
        )
        job_store.begin_running(job.id)
        before = float(job_store.get(job.id).params.get("last_progress_at") or 0)
        job_store.emit_progress(job.id, "Fetching deployments")
        after = float(job_store.get(job.id).params.get("last_progress_at") or 0)
        assert after >= before
        timeline = job_store.get(job.id).params.get("execution_timeline")
        assert isinstance(timeline, list)
        assert len(timeline) >= 1
    finally:
        job_store.clear_for_tests()
