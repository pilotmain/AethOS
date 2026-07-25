# SPDX-License-Identifier: Apache-2.0

from unittest.mock import patch

from aethos_core.operations.execution.execution_runner import run_vercel_readonly_execution


def test_logs_api_first_then_browser_fallback_message():
    params = {
        "target_name": "talking-avatar-agent",
        "operation_type": "check_logs",
        "auth_method": "api_token",
        "auth_method_label": "Vercel API token",
        "credential_id": "cred-test",
        "approved_actions": ["vercel_api_deployments", "vercel_logs_inspect"],
        "profile_id": "bprof-test",
    }
    dep_payload = {
        "ok": True,
        "source": "provider_api",
        "deployments": [{"id": "dpl_1", "state": "error"}],
        "output": "deployments",
    }
    log_payload = {
        "ok": False,
        "source": "provider_api",
        "api_limited": True,
        "error": "No log lines",
        "log_lines": [],
    }
    with patch(
        "aethos_core.operations.orchestration.registry_runtime.resolve_readonly_execution_adapter",
    ) as adapter_factory:
        adapter = adapter_factory.return_value
        adapter.get_deployments.return_value = dep_payload
        adapter.get_deployment_logs.return_value = log_payload
        with patch(
            "aethos_core.operations.execution.execution_runner._try_browser_log_excerpt",
            return_value=None,
        ):
            outcome = run_vercel_readonly_execution(params=params)
    assert outcome.artifact.data_source in ("provider_api", "memory")
    full = outcome.full_result
    assert "Read-only execution report" in full
    assert "Vercel API token" in full
    log_finding = next(f for f in outcome.artifact.findings if f.get("action") == "vercel_logs_inspect")
    assert "No log lines" in log_finding.get("output", "")
