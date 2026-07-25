# SPDX-License-Identifier: Apache-2.0

from unittest.mock import MagicMock, patch

from aethos_core.operations.execution.execution_runner import run_vercel_readonly_execution


def test_logs_execution_api_first_skips_browser_when_runtime_blocked():
    adapter = MagicMock()
    adapter.get_deployments.return_value = {
        "ok": True,
        "source": "provider_api",
        "deployments": [{"id": "dpl_1", "state": "error"}],
        "output": "deployments",
    }
    adapter.get_deployment_logs.return_value = {
        "ok": False,
        "source": "provider_api",
        "api_limited": True,
        "error": "No log lines",
        "log_lines": [],
        "output": "No log lines",
    }
    with patch(
        "aethos_core.operations.execution.execution_runner._resolve_vercel_adapter",
        return_value=(adapter, "api_token", "Vercel API token", "cred-1"),
    ), patch(
        "aethos_core.operations.execution.execution_runner.merge_project_state",
        return_value={},
    ), patch(
        "aethos_core.operations.execution.execution_runner.should_attempt_browser_fallback",
        return_value=False,
    ), patch(
        "aethos_core.operations.execution.execution_runner._try_browser_log_excerpt",
    ) as browser:
        outcome = run_vercel_readonly_execution(
            params={
                "target_name": "talking-avatar-agent",
                "operation_type": "why_down",
                "approved_actions": [
                    "vercel_api_deployments",
                    "url_reachability",
                    "vercel_logs_inspect",
                ],
                "auth_method": "api_token",
                "credential_id": "cred-1",
            }
        )
    browser.assert_not_called()
    adapter.get_deployment_logs.assert_called_once()
    log_finding = next(f for f in outcome.artifact.findings if f.get("action") == "vercel_logs_inspect")
    assert "Playwright is blocked" in log_finding.get("output", "")


def test_logs_execution_uses_browser_fallback_when_runtime_available():
    adapter = MagicMock()
    adapter.get_deployments.return_value = {
        "ok": True,
        "source": "provider_api",
        "deployments": [{"id": "dpl_1", "state": "error"}],
        "output": "deployments",
    }
    adapter.get_deployment_logs.return_value = {
        "ok": False,
        "source": "provider_api",
        "api_limited": True,
        "error": "No log lines",
        "log_lines": [],
        "output": "No log lines",
    }
    with patch(
        "aethos_core.operations.execution.execution_runner._resolve_vercel_adapter",
        return_value=(adapter, "api_token", "Vercel API token", "cred-1"),
    ), patch(
        "aethos_core.operations.execution.execution_runner.merge_project_state",
        return_value={},
    ), patch(
        "aethos_core.operations.execution.execution_runner.should_attempt_browser_fallback",
        return_value=True,
    ), patch(
        "aethos_core.operations.execution.execution_runner._try_browser_log_excerpt",
        return_value="Deployments page excerpt",
    ) as browser:
        outcome = run_vercel_readonly_execution(
            params={
                "target_name": "talking-avatar-agent",
                "operation_type": "check_logs",
                "approved_actions": ["vercel_api_deployments", "vercel_logs_inspect"],
                "auth_method": "api_token",
                "credential_id": "cred-1",
                "profile_id": "bprof-1",
            }
        )
    browser.assert_called_once()
    assert outcome.artifact.data_source == "browser_fallback"
