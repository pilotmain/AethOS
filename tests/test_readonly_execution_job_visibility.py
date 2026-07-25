# SPDX-License-Identifier: Apache-2.0

from aethos_core.runtime.jobs import job_store


def test_readonly_execution_jobs_partitioned_from_tracked_work():
    job_store.clear_for_tests()
    preflight = job_store.create(
        title="Preflight",
        job_type="vercel_domains_preflight",
        params={},
        auto_run=False,
    )
    execution = job_store.create(
        title="Read-only execution",
        job_type="readonly_execution_vercel",
        params={"operation_type": "list_domains", "target_name": "invoicepilot"},
        auto_run=False,
    )
    job_store.complete_with_result(
        preflight.id,
        full_result="# Preflight",
        summary="Preflight done",
        preview="Preflight done",
        provider="preflight",
        model="deterministic",
        used_llm=False,
        fallback=False,
    )
    job_store.complete_with_result(
        execution.id,
        full_result="# Execution",
        summary="Execution done",
        preview="Execution done",
        provider="readonly_execution",
        model="sandbox",
        used_llm=False,
        fallback=False,
    )
    grouped = job_store.list_grouped()
    completed_types = {j["job_type"] for j in grouped["completed"]}
    assert "readonly_execution_vercel" in completed_types
    assert "vercel_domains_preflight" in completed_types
    job_store.clear_for_tests()


def test_readonly_execution_job_has_visibility_fields_on_start():
    job_store.clear_for_tests()
    job = job_store.create(
        title="Read-only execution",
        job_type="readonly_execution_vercel",
        params={"operation_type": "why_down"},
        auto_run=False,
    )
    job_store.begin_running(job.id)
    running = job_store.get(job.id)
    assert running is not None
    assert running.params.get("started_at")
    assert running.params.get("last_progress_at")
    assert running.params.get("timeout_sec")
    job_store.clear_for_tests()
