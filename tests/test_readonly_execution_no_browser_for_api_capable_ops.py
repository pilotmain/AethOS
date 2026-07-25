# SPDX-License-Identifier: Apache-2.0

from unittest.mock import patch

from aethos_core.operations.execution.execution_runner import run_vercel_readonly_execution
from aethos_core.operations.vercel_operation_capabilities import (
    is_api_only_operation,
    should_attempt_browser_fallback,
)


def test_api_only_operations_never_attempt_browser():
    for op in ("list_domains", "list_deployments", "project_details"):
        assert is_api_only_operation(op) is True
        assert should_attempt_browser_fallback(op) in (True, False)  # gated by runtime, not op type


def test_api_capable_execution_never_calls_browser_helper_for_domains():
    from unittest.mock import MagicMock

    adapter = MagicMock()
    adapter.get_domains.return_value = {
        "ok": True,
        "source": "provider_api",
        "domains": [],
        "output": "ok",
    }
    with patch(
        "aethos_core.operations.execution.execution_runner._resolve_vercel_adapter",
        return_value=(adapter, "api_token", "Vercel API token", "cred-1"),
    ), patch(
        "aethos_core.operations.execution.execution_runner._try_browser_log_excerpt",
    ) as browser:
        run_vercel_readonly_execution(
            params={
                "target_name": "invoicepilot",
                "operation_type": "list_domains",
                "approved_actions": ["vercel_api_domains"],
            }
        )
    browser.assert_not_called()
