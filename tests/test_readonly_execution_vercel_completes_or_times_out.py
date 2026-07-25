# SPDX-License-Identifier: Apache-2.0

from unittest.mock import MagicMock, patch

from aethos_core.operations.execution.execution_runner import run_vercel_readonly_execution
from aethos_core.runtime.job_executor import job_executor
from aethos_core.runtime.jobs import JobStatus, job_store


def test_readonly_execution_vercel_completes_with_artifact():
    adapter = MagicMock()
    adapter.get_deployments.return_value = {
        "ok": True,
        "source": "provider_api",
        "project_id": "prj_1",
        "deployments": [{"id": "dpl_x", "state": "error", "error_message": "build failed"}],
        "output": "deployments",
    }
    adapter.get_deployment_logs.return_value = {
        "ok": True,
        "source": "provider_api",
        "deployment_id": "dpl_x",
        "events": [],
        "log_lines": ["build failed"],
        "output": "logs",
    }
    job_store.clear_for_tests()
    job_executor.drain_queue_for_tests()
    try:
        job = job_store.create(
            title="Read-only execution — why down (demo)",
            job_type="readonly_execution_vercel",
            params={
                "target_name": "demo",
                "operation_type": "why_down",
                "approved_actions": ["vercel_api_deployments", "url_reachability", "vercel_logs_inspect"],
                "auth_method": "api_token",
                "credential_id": "cred-1",
                "production_url": "https://demo.vercel.app",
            },
            auto_run=False,
        )
        with patch(
            "aethos_core.operations.execution.execution_runner._resolve_vercel_adapter",
            return_value=(adapter, "api_token", "Vercel API token", "cred-1"),
        ), patch(
            "aethos_core.operations.execution.execution_runner.merge_project_state",
            return_value={"production_url": "demo.vercel.app"},
        ), patch(
            "aethos_core.operations.execution.execution_runner._url_reachability",
            return_value={"url": "https://demo.vercel.app", "reachable": True, "summary": "HTTP 200"},
        ), patch(
            "aethos_core.operations.execution.execution_runner.should_attempt_browser_fallback",
            return_value=False,
        ):
            job_executor._execute_one(job.id)
        done = job_store.get(job.id)
        assert done is not None
        assert done.status == JobStatus.COMPLETED
        assert done.params.get("readonly_execution")
        assert done.full_result
        events = job_store.list_events(job_ids=[job.id])
        assert "job_completed" in [e["event_type"] for e in events]
    finally:
        job_store.clear_for_tests()
        job_executor.drain_queue_for_tests()


def test_readonly_execution_vercel_times_out_structured():
    job_store.clear_for_tests()
    job_executor.drain_queue_for_tests()
    try:
        job = job_store.create(
            title="Read-only execution — why down (slow)",
            job_type="readonly_execution_vercel",
            params={"target_name": "demo", "operation_type": "why_down", "approved_actions": []},
            auto_run=False,
        )

        def _hang(**_kwargs):
            import time

            time.sleep(5)

        with patch(
            "aethos_core.operations.execution.execution_runner.run_vercel_readonly_execution",
            side_effect=_hang,
        ), patch("aethos_core.runtime.job_executor.get_settings") as mock_settings:
            mock_settings.return_value.readonly_execution_timeout_sec = 0.2
            mock_settings.return_value.vercel_api_step_timeout_sec = 45.0
            mock_settings.return_value.url_reachability_timeout_sec = 12.0
            mock_settings.return_value.browser_fallback_step_timeout_sec = 20.0
            mock_settings.return_value.job_max_runtime_sec = 300.0
            mock_settings.return_value.job_provider_timeout_sec = 90.0
            job_executor._execute_one(job.id)

        failed = job_store.get(job.id)
        assert failed is not None
        assert failed.status == JobStatus.FAILED
        assert failed.params.get("status_reason") == "execution_timed_out"
    finally:
        job_store.clear_for_tests()
        job_executor.drain_queue_for_tests()
