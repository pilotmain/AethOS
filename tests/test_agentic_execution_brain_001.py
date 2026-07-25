# SPDX-License-Identifier: Apache-2.0
"""AGENTIC_EXECUTION_BRAIN_001 regression tests."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from aethos_core.chat.service import resolve_chat_turn
from aethos_core.execution_brain.execution_brain_router import route_execution_brain_turn
from aethos_core.execution_brain.execution_goal import detect_execution_goal, is_execution_brain_goal
from aethos_core.execution_brain.execution_memory import clear_execution_memory_for_tests
from aethos_core.execution_brain.execution_recovery_engine import recovery_path_for_blocker
from aethos_core.execution_brain.provider_tool_registry import list_provider_tools, tools_for_goal
from aethos_core.provider_e2e_readiness.blocker_mapping import ReadinessBlocker
from aethos_core.runtime.jobs import job_store

RAILWAY_DEPLOY = "Deploy AethOS to Railway."
RAILWAY_DEPLOY_ENV = "Deploy AethOS to Railway and configure env vars."
RAILWAY_READINESS = "Check if AethOS is ready to deploy to Railway."


@pytest.fixture(autouse=True)
def _reset_state():
    clear_execution_memory_for_tests()
    job_store.clear_for_tests()
    yield
    clear_execution_memory_for_tests()
    job_store.clear_for_tests()


def test_execution_goal_detection():
    goal = detect_execution_goal(RAILWAY_DEPLOY)
    assert goal is not None
    assert goal.provider == "railway"
    assert goal.action == "deploy"
    assert is_execution_brain_goal(RAILWAY_DEPLOY_ENV)
    assert not is_execution_brain_goal(RAILWAY_READINESS)


def test_railway_tool_registry():
    tools = list_provider_tools("railway")
    assert any(t.tool_id == "railway.validate_token" for t in tools)
    plan = tools_for_goal(provider="railway", requires_env=True, requires_verify=False)
    assert plan[0] == "railway.validate_token"
    assert "railway.create_deploy_preflight" in plan


def test_recovery_engine_token_invalid_narrative():
    blocker = ReadinessBlocker(
        code="RAILWAY_TOKEN_INVALID",
        meaning="Railway API rejected the configured token.",
        required_action="Replace token.",
        safe_next_command="validate Railway connection",
    )
    recovery = recovery_path_for_blocker(blocker)
    assert "token validation failed" in recovery.headline.lower()
    assert recovery.post_recovery_steps


def test_railway_brain_blocked_recovery_not_static_report():
    with patch(
        "aethos_core.providers.railway.deployment_readiness.deployment_readiness_checks._resolve_railway_token_canonical",
        return_value=(None, "test", "missing"),
    ):
        result = route_execution_brain_turn(RAILWAY_DEPLOY, session_id="brain-blocked")
    assert result is not None
    body, intent, meta = result
    assert intent == "execution_brain_recovery"
    assert "RAILWAY_TOKEN_MISSING" in body or "not configured" in body.lower()
    assert "After that succeeds I can" in body
    assert meta.get("mutation_performed") == "false"


def test_railway_brain_chat_route_no_generic_llm(monkeypatch):
    monkeypatch.setenv("PROVIDER_E2E_ORCHESTRATION_ENABLED", "false")
    from aethos_core.config import get_settings

    get_settings.cache_clear()
    with patch(
        "aethos_core.providers.railway.deployment_readiness.deployment_readiness_checks._resolve_railway_token_canonical",
        return_value=(None, "test", "missing"),
    ):
        result = resolve_chat_turn(RAILWAY_DEPLOY_ENV, session_id="brain-chat", apply_relational_layer=False)
    get_settings.cache_clear()
    assert result.used_llm is False
    assert result.intent == "execution_brain_recovery"
    assert "help plan" not in result.reply.lower()
    assert "capability truth" not in result.reply.lower()


def test_readiness_prompt_not_hijacked_by_brain():
    with patch(
        "aethos_core.providers.railway.deployment_readiness.deployment_readiness_checks._resolve_railway_token_canonical",
        return_value=(None, "test", "missing"),
    ):
        result = resolve_chat_turn(RAILWAY_READINESS, session_id="brain-readiness", apply_relational_layer=False)
    assert result.intent == "provider_e2e_readiness_report"


@patch("aethos_core.provider_e2e_execution.railway_e2e_execution.route_railway_e2e_execution")
@patch("aethos_core.providers.railway.deployment_readiness.deployment_readiness_checks.run_deployment_readiness_checks")
def test_railway_brain_creates_preflight_on_success(mock_checks, mock_e2e):
    mock_checks.return_value = {
        "railway_credential_ok": True,
        "railway_api_connection_ok": True,
        "inventory": {
            "ok": True,
            "project_count": 1,
            "service_count": 1,
            "projects": [
                {
                    "name": "aethos",
                    "environments": [{"name": "production", "services": ["aethos-api"]}],
                }
            ],
        },
        "service_creation": {"env_var_writes_enabled": True},
    }
    mock_e2e.return_value = (
        "preflight created",
        "railway_e2e_orchestration_preflight",
        {"job_id": "job-brain-1", "route_id": "railway_e2e_execution"},
    )
    result = route_execution_brain_turn(RAILWAY_DEPLOY_ENV, session_id="brain-preflight")
    assert result is not None
    body, intent, meta = result
    assert intent == "execution_brain_preflight_created"
    assert "job-brain-1" in body
    assert meta.get("preflight_created") == "true"
    assert meta.get("mutation_performed") == "false"


def test_brain_disabled_falls_through(monkeypatch):
    monkeypatch.setenv("EXECUTION_BRAIN_ENABLED", "false")
    from aethos_core.config import get_settings

    get_settings.cache_clear()
    assert route_execution_brain_turn(RAILWAY_DEPLOY) is None
    get_settings.cache_clear()
