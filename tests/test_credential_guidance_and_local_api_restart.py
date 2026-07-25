# SPDX-License-Identifier: Apache-2.0
"""HOTFIX 92A — credential guidance and local API restart routing."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from aethos_core.chat.explicit_mutation_intent import detect_explicit_mutation_intent
from aethos_core.chat.local_system_guidance import (
    is_local_aethos_api_restart_intent,
    route_local_system_guidance,
)
from aethos_core.chat.mutation_preflight_prompts import create_mutation_preflight_job_reply
from aethos_core.chat.service import resolve_chat_turn
from aethos_core.credentials.credential_guidance import (
    compose_railway_token_configuration_reply,
    is_railway_token_configuration_intent,
    route_railway_token_configuration_guidance,
)
from aethos_core.providers.railway.deployment_readiness.deployment_readiness_context import clear_for_tests


def setup_function() -> None:
    clear_for_tests()


def test_configure_railway_token_gives_exact_env_key() -> None:
    assert is_railway_token_configuration_intent("Configure Railway mutation token")
    result = route_railway_token_configuration_guidance("Configure Railway API token for Railway")
    assert result is not None
    body, intent, meta = result
    assert intent == "railway_token_configuration_guidance"
    assert "RAILWAY_API_TOKEN=..." in body
    assert "`.env`" in body
    assert "Credential Center → Providers → Railway" in body
    assert "restart the AethOS API process" in body
    assert "aethos_core.credentials import get_provider_api_token" in body
    assert meta.get("credential_key") == "RAILWAY_API_TOKEN"
    assert "No mutation has been performed." in body


def test_compose_railway_token_configuration_reply_shape() -> None:
    body = compose_railway_token_configuration_reply()
    assert "RAILWAY_API_TOKEN" in body
    assert "No mutation has been performed." in body


def test_restart_aethos_api_gives_local_guidance() -> None:
    assert is_local_aethos_api_restart_intent("Restart AethOS API")
    result = route_local_system_guidance("Restart AethOS API", session_id="local-92a")
    assert result is not None
    body, intent, meta = result
    assert intent == "local_system_api_restart_guidance"
    assert meta["route_id"] == "local_system_guidance"
    assert "uvicorn" in body
    assert "aethos_core.api.main:app" in body
    assert "Could not confirm a Railway service" not in body
    assert "No Railway mutation" in body


def test_restart_railway_pilotos_api_not_local_guidance() -> None:
    assert not is_local_aethos_api_restart_intent("restart pilotos-api in railway")
    assert detect_explicit_mutation_intent("restart pilotos-api in railway") is not None


@patch("aethos_core.chat.mutation_target_chat.gate_railway_mutation_preflight")
@patch("aethos_core.operations.mutations.preflight.run_mutation_preflight")
def test_no_mutation_preflight_for_local_api_restart(mock_preflight, mock_gate) -> None:
    mock_gate.return_value = ({"provider": "railway"}, None)
    result = create_mutation_preflight_job_reply("Restart AethOS API", session_id="no-preflight")
    assert result is None
    mock_preflight.assert_not_called()


@patch("aethos_core.providers.railway.deployment_readiness.deployment_readiness_checks.run_deployment_readiness_checks")
def test_readiness_reports_token_fail_until_loaded(mock_run) -> None:
    mock_run.return_value = {
        "readonly_readiness_ok": False,
        "referenced_github_repo": "",
        "railway_credential_ok": False,
        "railway_api_connection_ok": False,
        "railway_credential_detail": "missing Railway API token",
        "required_env_vars": ["RAILWAY_API_TOKEN"],
        "inventory": {"ok": False, "error": "no token"},
        "github_binding": {"github_credential_ok": False},
        "service_creation": {},
        "execution_mode": "api",
    }
    from aethos_core.providers.railway.deployment_readiness.deployment_readiness_safe_runtime import (
        safe_route_railway_deployment_readiness,
    )

    result = safe_route_railway_deployment_readiness("run railway deployment readiness", session_id="tok-fail")
    assert result is not None
    body, intent, _meta = result
    assert intent == "railway_deployment_readiness_blocked"
    assert "Railway token: **fail**" in body


@patch("aethos_core.operations.mutations.preflight.run_mutation_preflight")
@patch("aethos_core.chat.mutation_target_chat.gate_railway_mutation_preflight")
def test_resolve_chat_turn_local_restart_not_railway_clarification(mock_gate, mock_preflight) -> None:
    mock_gate.return_value = (None, "Could not confirm a Railway service matching **aethos**.")
    result = resolve_chat_turn("Restart AethOS API", session_id="chat-92a", apply_relational_layer=False)
    assert result.intent == "local_system_api_restart_guidance"
    assert "uvicorn" in result.reply
    assert "Could not confirm a Railway service" not in result.reply
    mock_preflight.assert_not_called()


@pytest.mark.parametrize(
    "prompt",
    [
        "Configure Railway mutation token",
        "set up railway api token",
    ],
)
def test_token_config_via_chat(prompt: str) -> None:
    result = resolve_chat_turn(prompt, session_id="cred-92a", apply_relational_layer=False)
    assert result.intent == "railway_token_configuration_guidance"
    assert "RAILWAY_API_TOKEN" in result.reply
