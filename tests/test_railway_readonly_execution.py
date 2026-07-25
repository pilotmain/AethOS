# SPDX-License-Identifier: Apache-2.0

from unittest.mock import MagicMock, patch

from aethos_core.operations.execution.railway_execution_runner import run_railway_readonly_execution


def test_railway_list_deployments_execution():
    adapter = MagicMock()
    adapter.get_deployments.return_value = {
        "ok": True,
        "source": "provider_api",
        "deployments": [
            {
                "id": "dep-1",
                "state": "success",
                "branch": "main",
                "commit": "abc123",
            }
        ],
        "output": "deployments markdown",
    }
    with patch(
        "aethos_core.operations.orchestration.registry_runtime.resolve_readonly_execution_adapter",
        return_value=adapter,
    ):
        outcome = run_railway_readonly_execution(
            params={
                "target_name": "api-worker",
                "operation_type": "list_deployments",
                "approved_actions": ["railway_api_deployments"],
                "auth_method": "api_token",
                "credential_id": "cred-1",
            }
        )
    assert outcome.artifact.provider == "railway"
    assert outcome.artifact.data_source == "provider_api"
    assert any(f.get("action") == "railway_api_deployments" for f in outcome.artifact.findings)
    assert outcome.artifact.confidence == "confirmed"
    assert any(e.get("source") == "railway_api" for e in outcome.artifact.evidence)


def test_railway_project_details_execution():
    adapter = MagicMock()
    adapter.get_project_details.return_value = {
        "ok": True,
        "source": "provider_api",
        "details": {
            "service_id": "svc-1",
            "service_name": "speakglobal-ai",
            "project_id": "proj-1",
            "project_name": "adequate-luck",
            "services_in_project": ["speakglobal-ai"],
        },
        "output": "Service: speakglobal-ai\nProject: adequate-luck",
    }
    with patch(
        "aethos_core.operations.orchestration.registry_runtime.resolve_readonly_execution_adapter",
        return_value=adapter,
    ):
        outcome = run_railway_readonly_execution(
            params={
                "target_name": "speakglobal-ai",
                "operation_type": "project_details",
                "approved_actions": ["railway_api_project_details"],
                "auth_method": "api_token",
                "credential_id": "cred-1",
            }
        )
    assert outcome.artifact.confidence == "confirmed"
    assert any(e.get("source") == "railway_api" and e.get("type") == "service_details" for e in outcome.artifact.evidence)
    assert "adequate-luck" in (outcome.full_result or "")


def test_railway_execution_timeout_is_structured():
    from aethos_core.operations.execution.execution_step_timeouts import ExecutionStepTimeoutError

    adapter = MagicMock()
    with patch(
        "aethos_core.operations.orchestration.registry_runtime.resolve_readonly_execution_adapter",
        return_value=adapter,
    ), patch(
        "aethos_core.operations.execution.railway_execution_runner._run_step",
        side_effect=ExecutionStepTimeoutError("railway_api_deployments", timeout_sec=30),
    ):
        outcome = run_railway_readonly_execution(
            params={
                "target_name": "api-worker",
                "operation_type": "list_deployments",
                "approved_actions": ["railway_api_deployments"],
                "auth_method": "api_token",
                "credential_id": "cred-1",
            }
        )
    assert any("error" in str(f.get("output", "")).lower() for f in outcome.artifact.findings)
