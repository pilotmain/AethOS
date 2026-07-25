# SPDX-License-Identifier: Apache-2.0

import os
from unittest.mock import patch

from fastapi.testclient import TestClient

from aethos_core.operations.intents import infer_operation_preflight_intent


@patch("aethos_core.provider.completion.complete_chat")
@patch("aethos_core.providers.vercel.auth.VercelAuthAdapter.resolve_best_auth_method")
@patch(
    "aethos_core.operational_planner.adapters.railway_wide_health.collect_railway_service_health_rows",
    return_value=([], "token missing"),
)
def test_failure_diagnostic_prompts_never_invoke_provider(mock_rows, mock_auth, mock_complete):
    mock_auth.return_value = {"method": "api_token", "credential_id": "cred-1"}
    mock_complete.side_effect = AssertionError("provider lane must not run for failure diagnostics")

    from aethos_core.api.main import app

    prompts = [
        "why did talking-avatar-agent fail",
        "why is quotepilot failing",
        "why did latest deploy fail",
        "what failed in lifeos",
    ]
    os.environ["BROWSER_AUTOMATION_ENABLED"] = "false"
    try:
        from aethos_core.config import get_settings

        get_settings.cache_clear()
        get_settings()
        client = TestClient(app)
        for prompt in prompts:
            assert infer_operation_preflight_intent(prompt) is None, prompt
            r = client.post("/api/v1/chat", json={"message": prompt, "session_id": "no-prov-fail"})
            body = r.json()
            assert body["used_llm"] is False, prompt
            assert body["intent"] in {
                "failed_service_investigation_discovery_failed",
                "failed_service_investigation_not_found",
                "failed_service_investigation_missing_report",
            }, prompt
            assert (body.get("meta") or {}).get("route_id") == "failed_service_preemption", prompt
            assert "Created tracked preflight job" not in body["reply"], prompt
            assert "vercel" not in body["reply"].lower(), prompt
        mock_complete.assert_not_called()
    finally:
        os.environ.pop("BROWSER_AUTOMATION_ENABLED", None)
        from aethos_core.config import get_settings

        get_settings.cache_clear()
