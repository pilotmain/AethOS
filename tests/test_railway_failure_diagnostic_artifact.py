# SPDX-License-Identifier: Apache-2.0

from unittest.mock import MagicMock, patch

from aethos_core.operations.execution.execution_evidence import CONFIDENCE_CONFIRMED
from aethos_core.operations.execution.railway_execution_runner import run_railway_readonly_execution


def test_railway_failure_diagnostic_artifact_has_evidence():
    adapter = MagicMock()
    adapter.get_deployments.return_value = {
        "ok": True,
        "source": "provider_api",
        "deployments": [
            {
                "id": "dep_failed",
                "state": "failed",
                "branch": "main",
                "commit": "abc123",
                "error_message": "Build failed: missing DATABASE_URL",
            }
        ],
        "output": "deployments markdown",
    }
    adapter.get_deployment_logs.return_value = {
        "ok": True,
        "source": "provider_api",
        "deployment_id": "dep_failed",
        "event_count": 1,
        "events": [{"type": "log", "text": "Build failed: missing DATABASE_URL"}],
        "log_lines": ["Build failed: missing DATABASE_URL"],
        "deployment": {"id": "dep_failed", "state": "failed", "error_message": "Build failed: missing DATABASE_URL"},
        "output": "logs markdown",
    }
    with patch(
        "aethos_core.operations.orchestration.registry_runtime.resolve_readonly_execution_adapter",
        return_value=adapter,
    ):
        outcome = run_railway_readonly_execution(
            params={
                "target_name": "api-worker",
                "operation_type": "why_down",
                "approved_actions": ["railway_api_deployments", "railway_api_logs"],
                "auth_method": "api_token",
                "credential_id": "cred-1",
            }
        )

    artifact = outcome.artifact
    assert artifact.confidence in (CONFIDENCE_CONFIRMED, "likely", "possible")
    assert artifact.evidence
    assert artifact.diagnostic or artifact.probable_root_cause
