# SPDX-License-Identifier: Apache-2.0

from aethos_core.operations.preflight_execution import approve_preflight_readonly_execution
from aethos_core.runtime.jobs import job_store


def test_preflight_links_execution_job_id(tmp_path, monkeypatch):
    monkeypatch.setenv("BROWSER_PROFILES_DIR", str(tmp_path / "browser_profiles"))
    job_store.clear_for_tests()
    try:
        preflight = job_store.create(
            title="Vercel domains preflight",
            job_type="vercel_domains_preflight",
            params={
                "user_request": "show domains for invoicepilot",
                "provider": "vercel",
                "operation_type": "list_domains",
                "operation_preflight": {
                    "provider": "vercel",
                    "operation_type": "list_domains",
                    "target_name": "invoicepilot",
                    "target_status": "resolved",
                    "preflight_status": "ready_for_readonly_diagnostic",
                    "read_only_execution_enabled": True,
                },
                "preflight_status": "ready_for_readonly_diagnostic",
            },
            auto_run=False,
        )
        job_store.complete_with_result(
            preflight.id,
            full_result="# Preflight",
            summary="ready",
            preview="ready",
            provider="preflight",
            model="deterministic",
            used_llm=False,
            fallback=False,
        )
        pf_job, exec_job = approve_preflight_readonly_execution(preflight.id)
        assert pf_job.params.get("execution_job_id") == exec_job.id
        pf = pf_job.params.get("operation_preflight") or {}
        assert pf.get("execution_job_id") == exec_job.id
        assert exec_job.params.get("source_preflight_job_id") == preflight.id
    finally:
        job_store.clear_for_tests()
