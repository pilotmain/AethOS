# SPDX-License-Identifier: Apache-2.0

from unittest.mock import MagicMock, patch

from aethos_core.operations.execution.execution_runner import run_vercel_readonly_execution


def test_domains_execution_uses_api_only():
    adapter = MagicMock()
    adapter.get_domains.return_value = {
        "ok": True,
        "source": "provider_api",
        "domains": [{"domain": "invoicepilot.com", "verified": True, "production": True}],
        "output": "Project: invoicepilot\nDomains (1):",
    }
    with patch(
        "aethos_core.operations.execution.execution_runner._resolve_vercel_adapter",
        return_value=(adapter, "api_token", "Vercel API token", "cred-1"),
    ), patch(
        "aethos_core.operations.execution.execution_runner._try_browser_log_excerpt",
    ) as browser:
        outcome = run_vercel_readonly_execution(
            params={
                "target_name": "invoicepilot",
                "operation_type": "list_domains",
                "approved_actions": ["vercel_api_domains"],
                "auth_method": "api_token",
                "credential_id": "cred-1",
            }
        )
    browser.assert_not_called()
    adapter.get_domains.assert_called_once_with(project_name="invoicepilot")
    assert outcome.artifact.data_source == "provider_api"
    assert outcome.artifact.auth_method_label == "Vercel API token"
    assert "provider_api" in outcome.full_result.lower() or "Provider API execution" in outcome.full_result
    assert "No mutation performed" in outcome.full_result
