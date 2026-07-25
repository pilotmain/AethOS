# SPDX-License-Identifier: Apache-2.0

import os
from unittest.mock import patch

from fastapi.testclient import TestClient

from aethos_core.operations.intents import infer_operation_preflight_intent


@patch("aethos_core.providers.vercel.auth.VercelAuthAdapter.resolve_best_auth_method")
@patch(
    "aethos_core.operational_planner.adapters.railway_wide_health.collect_railway_service_health_rows",
    return_value=([], "token missing"),
)
def test_why_did_project_fail_routes_through_cognition_not_vercel(mock_rows, mock_auth):
    mock_auth.return_value = {"method": "api_token", "credential_id": "cred-1"}

    from aethos_core.api.main import app

    os.environ["BROWSER_AUTOMATION_ENABLED"] = "false"
    try:
        from aethos_core.config import get_settings

        get_settings.cache_clear()
        get_settings()
        client = TestClient(app)
        prompt = "why did talking-avatar-agent fail"
        assert infer_operation_preflight_intent(prompt) is None
        r = client.post("/api/v1/chat", json={"message": prompt, "session_id": "fail-route"})
        body = r.json()
        assert body["used_llm"] is False
        assert body["intent"] == "failed_service_investigation_discovery_failed"
        assert (body.get("meta") or {}).get("route_id") == "failed_service_preemption"
        assert (body.get("meta") or {}).get("cognition_intent") == "diagnose_failure"
        assert "Created tracked preflight job" not in body["reply"]
        assert "refresh" in body["reply"].lower() or "could not resolve" in body["reply"].lower()
    finally:
        os.environ.pop("BROWSER_AUTOMATION_ENABLED", None)
        from aethos_core.config import get_settings

        get_settings.cache_clear()


@patch("aethos_core.providers.vercel.auth.VercelAuthAdapter.resolve_best_auth_method")
@patch(
    "aethos_core.operational_planner.adapters.railway_wide_health.collect_railway_service_health_rows",
    return_value=([], "token missing"),
)
def test_failure_variants_route_through_cognition_not_vercel(mock_rows, mock_auth):
    mock_auth.return_value = {"method": "api_token", "credential_id": "cred-1"}

    from aethos_core.api.main import app

    prompts = [
        "why is quotepilot failing",
        "why did latest deploy fail",
        "what failed in lifeos",
    ]
    try:
        from aethos_core.config import get_settings

        get_settings.cache_clear()
        get_settings()
        client = TestClient(app)
        for prompt in prompts:
            assert infer_operation_preflight_intent(prompt) is None, prompt
            r = client.post("/api/v1/chat", json={"message": prompt, "session_id": f"fail-{prompt[:8]}"})
            body = r.json()
            assert body["used_llm"] is False, prompt
            assert body["intent"] in {
                "failed_service_investigation_discovery_failed",
                "failed_service_investigation_not_found",
            }, prompt
            assert (body.get("meta") or {}).get("provider") != "vercel", prompt
            assert "Created tracked preflight job" not in body["reply"], prompt
    finally:
        from aethos_core.config import get_settings

        get_settings.cache_clear()
