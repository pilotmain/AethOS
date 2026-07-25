# SPDX-License-Identifier: Apache-2.0

from unittest.mock import patch

from aethos_core.browser.platforms.vercel.vercel_entities import HealthState, VercelInventoryArtifact, VercelProject
from aethos_core.operations.preflight import run_operation_preflight
from aethos_core.operations.preflight_execution import approve_preflight_readonly_execution
from aethos_core.runtime.job_executor import job_executor
from aethos_core.runtime.jobs import job_store
from aethos_core.runtime.operational_memory import operational_memory
from tests.job_test_utils import drain_job_executor


@patch("aethos_core.providers.vercel.auth.VercelAuthAdapter.resolve_best_auth_method")
def test_preflight_report_mentions_execution_job_when_approved(mock_auth, tmp_path, monkeypatch):
    mock_auth.return_value = {"method": "api_token", "credential_id": "cred-1"}
    monkeypatch.setenv("BROWSER_PROFILES_DIR", str(tmp_path / "browser_profiles"))
    operational_memory.clear_for_tests()
    job_executor.drain_queue_for_tests()
    try:
        operational_memory.record_vercel_extraction(
            VercelInventoryArtifact(
                projects=[
                    VercelProject(
                        name="talking-avatar-agent",
                        health=HealthState.FAILED,
                        health_confidence="failed",
                    )
                ]
            ),
            profile_id="bprof-1",
        )
        outcome = run_operation_preflight(
            job_type="vercel_down_diagnostic_preflight",
            params={
                "user_request": "why did talking-avatar-agent fail",
                "provider": "vercel",
                "operation_type": "why_down",
                "target_hints": ["talking-avatar-agent"],
            },
        )
        job = job_store.create(
            title="Vercel down diagnostic preflight",
            job_type="vercel_down_diagnostic_preflight",
            params={
                "user_request": "why did talking-avatar-agent fail",
                "provider": "vercel",
                "operation_type": "why_down",
                "operation_preflight": outcome.preflight.to_dict(),
                "preflight_status": outcome.preflight.preflight_status,
            },
            auto_run=False,
        )
        job_store.complete_with_result(
            job.id,
            full_result=outcome.full_result,
            summary=outcome.summary,
            preview=outcome.preview,
            provider="preflight",
            model="deterministic",
            used_llm=False,
            fallback=False,
        )

        preflight_job, execution_job = approve_preflight_readonly_execution(job.id)
        assert execution_job.id.startswith("job-")
        assert preflight_job.params["execution_approved"] is True
        pf = preflight_job.params["operation_preflight"]
        assert pf["execution_approved"] is True
        assert pf["execution_job_id"] == execution_job.id
        assert f"**Execution job:** `{execution_job.id}`" in (preflight_job.full_result or "")
        assert "**Execution approved:** yes" in (preflight_job.full_result or "")

        drain_job_executor()
    finally:
        operational_memory.clear_for_tests()
        job_executor.drain_queue_for_tests()
