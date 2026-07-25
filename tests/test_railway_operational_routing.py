# SPDX-License-Identifier: Apache-2.0

import os
from unittest.mock import patch

from fastapi.testclient import TestClient

from aethos_core.operations.intents import infer_operation_preflight_intent


def test_railway_deployments_intent():
    out = infer_operation_preflight_intent("show railway deployments for api-worker")
    assert out is not None
    _, job_type, params = out
    assert job_type == "operation_preflight"
    assert params["provider"] == "railway"
    assert params["operation_type"] == "list_deployments"
    assert "api-worker" in params["target_hints"]


def test_railway_why_down_intent():
    out = infer_operation_preflight_intent("why is api-worker failing on railway")
    assert out is not None
    assert out[1] == "operation_preflight"
    assert out[2]["operation_type"] == "why_down"
    assert out[2]["provider"] == "railway"


@patch("aethos_core.providers.railway.auth.RailwayAuthAdapter.resolve_best_auth_method")
def test_railway_chat_routes_without_llm(mock_auth):
    mock_auth.return_value = {"method": "api_token", "credential_id": "cred-railway"}

    from aethos_core.api.main import app

    os.environ["BROWSER_AUTOMATION_ENABLED"] = "false"
    try:
        from aethos_core.config import get_settings

        get_settings.cache_clear()
        client = TestClient(app)
        prompt = "show railway deployments for api-worker"
        r = client.post("/api/v1/chat", json={"message": prompt, "session_id": "railway-route"})
        body = r.json()
        assert body["used_llm"] is False
        meta = body.get("meta") or {}
        assert meta.get("provider") == "railway"
        assert meta.get("operation_type") == "list_deployments"
        assert meta.get("proposed_job_type") == "operation_preflight"
    finally:
        os.environ.pop("BROWSER_AUTOMATION_ENABLED", None)
        from aethos_core.config import get_settings

        get_settings.cache_clear()
