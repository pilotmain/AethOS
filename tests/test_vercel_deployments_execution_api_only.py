# SPDX-License-Identifier: Apache-2.0

from unittest.mock import MagicMock, patch

from aethos_core.operations.execution.execution_runner import run_vercel_readonly_execution


def test_deployments_execution_uses_api_only():
    adapter = MagicMock()
    adapter.get_deployments.return_value = {
        "ok": True,
        "source": "provider_api",
        "deployments": [{"id": "dpl_1", "state": "ready", "target": "production", "branch": "main"}],
        "output": "Project: quotepilot",
    }
    with patch(
        "aethos_core.operations.execution.execution_runner._resolve_vercel_adapter",
        return_value=(adapter, "api_token", "Vercel API token", "cred-1"),
    ), patch(
        "aethos_core.operations.execution.execution_runner.merge_project_state",
        return_value={},
    ), patch(
        "aethos_core.operations.execution.execution_runner._try_browser_log_excerpt",
    ) as browser:
        outcome = run_vercel_readonly_execution(
            params={
                "target_name": "quotepilot",
                "operation_type": "list_deployments",
                "approved_actions": ["vercel_api_deployments", "url_reachability"],
                "auth_method": "api_token",
                "credential_id": "cred-1",
            }
        )
    browser.assert_not_called()
    adapter.get_deployments.assert_called_once()
    assert outcome.artifact.data_source == "provider_api"
