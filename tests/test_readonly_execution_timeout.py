# SPDX-License-Identifier: Apache-2.0

from time import time

from aethos_core.runtime.jobs import JobStatus, job_store


def test_stale_running_readonly_execution_is_reaped():
    job_store.clear_for_tests()
    try:
        job = job_store.create(
            title="Read-only execution",
            job_type="readonly_execution_vercel",
            params={"operation_type": "why_down"},
            auto_run=False,
        )
        job_store.begin_running(job.id)
        running = job_store.get(job.id)
        assert running is not None
        running.params["started_at"] = time() - 9999
        running.params["last_progress_at"] = time() - 9999
        running.params["timeout_sec"] = 30.0
        reaped = job_store.reap_stale_running_jobs()
        assert job.id in reaped
        failed = job_store.get(job.id)
        assert failed is not None
        assert failed.status == JobStatus.FAILED
        assert failed.params.get("status_reason") == "execution_timed_out"
        assert "timed out" in (failed.failure_reason or "").lower()
    finally:
        job_store.clear_for_tests()
