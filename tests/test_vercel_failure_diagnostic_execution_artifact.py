# SPDX-License-Identifier: Apache-2.0

from unittest.mock import MagicMock, patch

from aethos_core.operations.execution.execution_evidence import (
    CONFIDENCE_CONFIRMED,
    CONFIDENCE_INSUFFICIENT,
    select_failed_deployment,
)
from aethos_core.operations.execution.execution_runner import run_vercel_readonly_execution


def test_select_failed_deployment_prefers_failed_state():
    deps = [
        {"id": "dpl_ok", "state": "ready"},
        {"id": "dpl_bad", "state": "error", "error_message": "Build failed: missing env"},
    ]
    picked = select_failed_deployment(deps)
    assert picked is not None
    assert picked["id"] == "dpl_bad"


def test_failure_diagnostic_execution_artifact_has_structured_evidence():
    adapter = MagicMock()
    adapter.get_deployments.return_value = {
        "ok": True,
        "source": "provider_api",
        "deployments": [
            {
                "id": "dpl_failed123",
                "state": "error",
                "target": "production",
                "branch": "main",
                "commit": "abc123def456",
                "error_message": "Build failed: missing NEXT_PUBLIC_API_URL",
                "created_at": "2026-05-20T10:02:00Z",
            }
        ],
        "output": "deployments markdown",
    }
    adapter.get_deployment_logs.return_value = {
        "ok": True,
        "source": "provider_api",
        "deployment_id": "dpl_failed123",
        "event_count": 2,
        "events": [
            {"type": "stdout", "text": "Build failed: missing NEXT_PUBLIC_API_URL", "created": "2026-05-20T10:03:00Z"},
        ],
        "log_lines": ["Build failed: missing NEXT_PUBLIC_API_URL"],
        "output": "logs markdown",
        "deployment": {
            "id": "dpl_failed123",
            "state": "error",
            "target": "production",
            "error_message": "Build failed: missing NEXT_PUBLIC_API_URL",
        },
    }
    with patch(
        "aethos_core.operations.execution.execution_runner._resolve_vercel_adapter",
        return_value=(adapter, "api_token", "Vercel API token", "cred-1"),
    ), patch(
        "aethos_core.operations.execution.execution_runner.merge_project_state",
        return_value={
            "production_url": "talking-avatar-agent.vercel.app",
            "latest_deployment_state": "failed",
            "evidence": ["source:vercel_api"],
        },
    ), patch(
        "aethos_core.operations.execution.execution_runner._url_reachability",
        return_value={"url": "https://talking-avatar-agent.vercel.app", "reachable": True, "summary": "HTTP 200"},
    ), patch(
        "aethos_core.operations.execution.execution_runner.should_attempt_browser_fallback",
        return_value=False,
    ):
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

    artifact = outcome.artifact
    assert artifact.data_source == "provider_api"
    assert artifact.confidence == CONFIDENCE_CONFIRMED
    diag = artifact.diagnostic
    assert diag.get("failure_reason_confidence") == CONFIDENCE_CONFIRMED
    root = (artifact.probable_root_cause or "").lower()
    assert (
        "npm run build" in root
        or "build command" in root
        or "build failed" in root
        or "the api reports" in root
    )
    primary = (diag.get("evidence_by_tier") or {}).get("primary") or []
    assert any(e.get("type") == "failure_reason" for e in primary)
    assert artifact.operational_events
    assert "## Primary finding" in outcome.full_result
    assert "## Production impact" in outcome.full_result
    assert len(artifact.evidence) < 20


def test_failure_diagnostic_without_api_evidence_stays_conservative():
    with patch(
        "aethos_core.operations.execution.execution_runner._resolve_vercel_adapter",
        return_value=(None, "none", "none", ""),
    ), patch(
        "aethos_core.operations.execution.execution_runner.merge_project_state",
        return_value={"latest_deployment_state": "unknown", "evidence": []},
    ):
        outcome = run_vercel_readonly_execution(
            params={
                "target_name": "talking-avatar-agent",
                "operation_type": "why_down",
                "approved_actions": ["url_reachability"],
            }
        )
    assert outcome.artifact.confidence == CONFIDENCE_INSUFFICIENT
    assert "Insufficient evidence" in (outcome.artifact.probable_root_cause or "")
