# SPDX-License-Identifier: Apache-2.0
"""FIX 91 — Railway new-service deployment readiness."""

from __future__ import annotations

from unittest.mock import patch

from aethos_core.providers.railway.deployment_readiness.deployment_readiness_context import clear_for_tests
from aethos_core.providers.railway.deployment_readiness.deployment_readiness_intent import (
    is_railway_deployment_readiness_intent,
)
from aethos_core.providers.railway.deployment_readiness.deployment_readiness_router import (
    route_railway_deployment_readiness,
)
from aethos_core.chat.service import resolve_chat_turn


def setup_function() -> None:
    clear_for_tests()


def test_intent_detection() -> None:
    assert is_railway_deployment_readiness_intent("deploy a brand new railway service")
    assert is_railway_deployment_readiness_intent("run railway deployment readiness")
    assert is_railway_deployment_readiness_intent("can you deploy a new railway service")


def test_restart_not_readiness_lane() -> None:
    assert not is_railway_deployment_readiness_intent("restart pilotos-api in railway")


@patch("aethos_core.providers.railway.deployment_readiness.deployment_readiness_checks.run_deployment_readiness_checks")
def test_capability_truth_short_answer(mock_checks) -> None:
    mock_checks.return_value = {"readonly_readiness_ok": True, "inventory": {"ok": True, "project_count": 1}}
    result = route_railway_deployment_readiness(
        "can you deploy a brand new railway service?",
        session_id="cap-91",
    )
    assert result is not None
    body, intent, meta = result
    assert intent == "railway_new_service_capability"
    assert "existing" in body.lower() and "railway services" in body.lower()
    assert "readiness checks first" in body.lower()
    assert "no service will be created until" in body.lower()
    assert meta["route_id"] == "railway_deployment_readiness"


@patch("aethos_core.providers.railway.deployment_readiness.deployment_readiness_checks.run_deployment_readiness_checks")
def test_full_readiness_report(mock_checks) -> None:
    mock_checks.return_value = {
        "readonly_readiness_ok": True,
        "railway_credential_ok": True,
        "railway_api_connection_ok": True,
        "railway_credential_source": "env",
        "execution_mode": "api",
        "required_env_vars": ["RAILWAY_API_TOKEN"],
        "inventory": {
            "ok": True,
            "project_count": 1,
            "environment_count": 1,
            "service_count": 2,
            "projects": [{"name": "pilotos", "environments": [{"name": "production", "services": ["api"]}]}],
        },
        "github_binding": {"github_credential_ok": True, "accessible_repos_count": 3},
        "service_creation": {
            "graphql_service_create": False,
            "graphql_service_create_detail": "not wired",
            "governed_mutation_adapter_ops": ["restart", "redeploy"],
            "env_var_writes_enabled": False,
        },
        "mutation_ready": True,
    }
    result = route_railway_deployment_readiness("run railway deployment readiness", session_id="readiness-91")
    assert result is not None
    body, intent, meta = result
    assert intent == "railway_deployment_readiness"
    assert "Railway new-service deployment readiness" in body
    assert "Service creation API" in body
    assert "No Railway service has been created" in body
    assert meta.get("readonly_readiness_ok") == "true"


@patch("aethos_core.providers.railway.deployment_readiness.deployment_readiness_router.route_railway_deployment_readiness")
def test_resolve_chat_turn_routes_readiness(mock_route) -> None:
    mock_route.return_value = ("ready", "railway_deployment_readiness", {"route_id": "railway_deployment_readiness"})
    result = resolve_chat_turn("deploy a new railway service", session_id="chat-91", apply_relational_layer=False)
    assert result.intent == "railway_deployment_readiness"
    assert "How I can help" not in result.reply
    mock_route.assert_called_once()
