# SPDX-License-Identifier: Apache-2.0

from unittest.mock import patch

from aethos_core.connections.adapters import auth_method_label_for_provider
from aethos_core.operations.operation_models import OperationPreflight
from aethos_core.operations.preflight_summary import chat_summary_for_preflight
from aethos_core.operations.railway_preflight import build_railway_preflight, format_preflight_report
from aethos_core.operations.target_resolution import TargetResolution


def test_provider_auth_labels():
    assert auth_method_label_for_provider("railway", "api_token") == "Railway API token"
    assert auth_method_label_for_provider("vercel", "api_token") == "Vercel API token"


@patch("aethos_core.providers.railway.auth.RailwayAuthAdapter.resolve_best_auth_method")
def test_railway_preflight_summary_uses_railway_auth_label(mock_resolve):
    mock_resolve.return_value = {
        "method": "api_token",
        "credential_id": "cred-rw",
    }
    preflight = build_railway_preflight(
        operation_type="list_deployments",
        resolution=TargetResolution(
            status="resolved",
            target_name="speakglobal-ai",
            message="ok",
            matches=[],
        ),
        user_request="show railway deployments for speakglobal-ai",
    )
    summary = chat_summary_for_preflight(preflight)
    assert "Railway API token" in summary
    assert "Vercel API token" not in summary
    assert "speakglobal-ai" in summary
    assert "list deployments" in summary

    report = format_preflight_report(preflight)
    assert "Railway API token" in report
    assert "Vercel API token" not in report


def test_vercel_preflight_summary_still_uses_vercel_auth_label():
    preflight = OperationPreflight(
        provider="vercel",
        operation_type="list_deployments",
        target_name="invoicepilot",
        target_status="resolved",
        risk_level="low",
        preflight_status="ready_for_readonly_diagnostic",
        current_state={
            "api_capable": True,
            "auth_method": "api_token",
            "auth_method_label": "Vercel API token",
        },
        proposed_steps=["Check deployments"],
    )
    summary = chat_summary_for_preflight(preflight)
    assert "Vercel API token" in summary
    assert "Railway API token" not in summary
