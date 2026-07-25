# SPDX-License-Identifier: Apache-2.0

from unittest.mock import MagicMock, patch

from aethos_core.operations.execution.execution_runner import run_vercel_readonly_execution
from aethos_core.operations.execution.execution_step_timeouts import ExecutionStepTimeoutError


def test_partial_artifact_when_deployment_events_timeout():
    adapter = MagicMock()
    adapter.get_deployments.return_value = {
        "ok": True,
        "source": "provider_api",
        "project_id": "prj_1",
        "deployments": [{"id": "dpl_fail", "state": "error", "error_message": "npm run build exited with 1"}],
        "output": "deployments",
    }
    adapter.get_deployment_logs.side_effect = ExecutionStepTimeoutError(
        "vercel_logs_inspect", timeout_sec=45.0
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
        outcome = run_vercel_readonly_execution(
            params={
                "target_name": "demo",
                "operation_type": "why_down",
                "approved_actions": ["vercel_api_deployments", "url_reachability", "vercel_logs_inspect"],
                "auth_method": "api_token",
                "credential_id": "cred-1",
            }
        )

    assert outcome.artifact
    timed_out = any(
        (isinstance(f, dict) and (f.get("step_timed_out") or "timed out" in str(f.get("output", "")).lower()))
        for f in outcome.artifact.findings
    )
    assert timed_out
    assert outcome.full_result
