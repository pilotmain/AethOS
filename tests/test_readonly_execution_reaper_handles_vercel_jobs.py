# SPDX-License-Identifier: Apache-2.0

from time import time

from aethos_core.runtime.jobs import JobStatus, job_store


def test_reaper_only_fails_stale_readonly_execution_jobs():
    job_store.clear_for_tests()
    try:
        readonly = job_store.create(
            title="Read-only execution",
            job_type="readonly_execution_vercel",
            params={"operation_type": "why_down"},
            auto_run=False,
        )
        other = job_store.create(
            title="Research",
            job_type="research_plan",
            params={},
            auto_run=False,
        )
        job_store.begin_running(readonly.id)
        job_store.begin_running(other.id)
        ro = job_store.get(readonly.id)
        ot = job_store.get(other.id)
        assert ro and ot
        ro.params["started_at"] = time() - 9999
        ro.params["last_progress_at"] = time() - 9999
        ro.params["timeout_sec"] = 30.0
        ot.params["last_progress_at"] = time() - 9999

        reaped = job_store.reap_stale_running_jobs()
        assert readonly.id in reaped
        assert other.id not in reaped
        assert job_store.get(readonly.id).status == JobStatus.FAILED
        assert job_store.get(other.id).status == JobStatus.RUNNING
    finally:
        job_store.clear_for_tests()
