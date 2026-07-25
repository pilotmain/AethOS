# SPDX-License-Identifier: Apache-2.0
"""Provider readonly orchestration routing tests."""

from __future__ import annotations

from unittest.mock import patch

from aethos_core.chat.chat_turn_steps import try_operational_fast_path_turn
from aethos_core.provider_e2e_execution.provider_e2e_execution_intent import (
    is_provider_e2e_execution_intent,
    is_provider_readonly_orchestration_intent,
)
from aethos_core.provider_e2e_execution.provider_e2e_execution_service import route_provider_e2e_execution


VERCEL_LIST_HEALTH = "list all vercel projects and show deployment health for each"


def test_list_vercel_health_is_readonly_orchestration_not_e2e():
    assert is_provider_readonly_orchestration_intent(VERCEL_LIST_HEALTH) is True
    assert is_provider_e2e_execution_intent(VERCEL_LIST_HEALTH) is False
    assert route_provider_e2e_execution(VERCEL_LIST_HEALTH, session_id="orch-test") is None


def test_deploy_env_verify_still_e2e():
    text = "deploy killit on vercel configure env vars and verify health check"
    assert is_provider_e2e_execution_intent(text) is True


def test_list_vercel_health_not_e2e_missing_config(monkeypatch):
    from aethos_core.config import get_settings
    from aethos_core.chat.service import resolve_chat_turn

    monkeypatch.setattr(get_settings(), "agent_runtime_enabled", False)
    monkeypatch.setattr(get_settings(), "provider_e2e_orchestration_enabled", True)
    with patch(
        "aethos_core.operational_session.vercel_readonly_executor._resolve_token",
        lambda: ("token", "cred"),
    ), patch(
        "aethos_core.providers.vercel.diagnostics.project_diagnostics_api.fetch_projects_list",
        lambda token, limit=20: {"ok": True, "projects": [{"name": "killit", "latest_production_state": "READY"}]},
    ), patch(
        "aethos_core.providers.vercel.operations.deployments_api.fetch_deployments",
        lambda token, *, project_name, limit=3: {
            "ok": True,
            "deployments": [{"state": "READY", "url": "https://killit.vercel.app", "branch": "main"}],
        },
    ):
        result = resolve_chat_turn(VERCEL_LIST_HEALTH, session_id="list-health", apply_relational_layer=False)
    assert "missing configuration" not in result.reply.lower()
    assert result.intent.startswith("operational_kernel") or result.intent == "agent_runtime"


def test_operational_step_defers_to_agent_when_enabled(monkeypatch):
    from aethos_core.config import get_settings

    monkeypatch.setattr(get_settings(), "agent_runtime_enabled", True)
    result = try_operational_fast_path_turn(
        VERCEL_LIST_HEALTH,
        session_id="defer-agent",
        channel="chat",
        emotional_context=None,
    )
    assert result is None


def test_vercel_deployment_health_all_projects(monkeypatch):
    monkeypatch.setattr(
        "aethos_core.execution_brain.agent_tool_executor._resolve_vercel_token",
        lambda: ("token", "cred"),
    )

    def fake_list(token, *, limit=20):
        _ = token, limit
        return {"ok": True, "projects": [{"name": "killit"}, {"name": "pilotos"}]}

    def fake_deployments(token, *, project_name, limit=3):
        _ = token, limit
        return {
            "ok": True,
            "deployments": [{"state": "READY", "url": f"https://{project_name}.vercel.app", "branch": "main"}],
        }

    monkeypatch.setattr(
        "aethos_core.providers.vercel.diagnostics.project_diagnostics_api.fetch_projects_list",
        fake_list,
    )
    monkeypatch.setattr(
        "aethos_core.providers.vercel.operations.deployments_api.fetch_deployments",
        fake_deployments,
    )
    from aethos_core.execution_brain.agent_tool_executor import execute_agent_tool

    raw = execute_agent_tool("vercel_deployment_health", {}, session_id="tool-test")
    assert "killit" in raw
    assert "READY" in raw
