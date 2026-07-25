# SPDX-License-Identifier: Apache-2.0

from unittest.mock import MagicMock, patch

from aethos_core.operations.execution.execution_runner import run_vercel_readonly_execution


def test_project_details_execution_uses_api_only():
    adapter = MagicMock()
    adapter.get_project_details.return_value = {
        "ok": True,
        "source": "provider_api",
        "details": {"framework": "nextjs", "repo_link": "raya/lifeos"},
        "output": "Project: lifeos\n- Framework: nextjs",
    }
    with patch(
        "aethos_core.operations.execution.execution_runner._resolve_vercel_adapter",
        return_value=(adapter, "api_token", "Vercel API token", "cred-1"),
    ), patch(
        "aethos_core.operations.execution.execution_runner._try_browser_log_excerpt",
    ) as browser:
        outcome = run_vercel_readonly_execution(
            params={
                "target_name": "lifeos",
                "operation_type": "project_details",
                "approved_actions": ["vercel_api_project_details"],
                "auth_method": "api_token",
                "credential_id": "cred-1",
            }
        )
    browser.assert_not_called()
    adapter.get_project_details.assert_called_once_with(project_name="lifeos")
    assert "Vercel API token" in outcome.full_result
