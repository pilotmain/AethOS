# SPDX-License-Identifier: Apache-2.0
"""Agent runtime convergence tests."""

from __future__ import annotations

from unittest.mock import patch

from aethos_core.config import get_settings
from aethos_core.execution_brain.agent_runtime import run_agent_runtime_turn, should_use_agent_runtime
from aethos_core.execution_brain.agent_tool_executor import agent_tool_schemas, execute_agent_tool, readonly_agent_tool_schemas
from aethos_core.provider.completion import ToolLoopResult


def test_agent_runtime_disabled_by_default(monkeypatch):
    from aethos_core.config import get_settings

    monkeypatch.setattr(get_settings(), "agent_runtime_enabled", False)
    assert should_use_agent_runtime("compare redis vs postgres") is False


def test_agent_runtime_requires_flag_and_provider(monkeypatch):
    monkeypatch.setattr(get_settings(), "agent_runtime_enabled", True)
    monkeypatch.setattr(get_settings(), "use_real_llm", True)
    monkeypatch.setattr(get_settings(), "anthropic_api_key", "sk-test")
    assert should_use_agent_runtime("hello there") is True


def test_agent_tool_schemas_include_provider_cloud_tools():
    names = {t["name"] for t in readonly_agent_tool_schemas()}
    assert "web_search" in names
    assert "provider_validate" in names
    assert "provider_create_mutation_preflight" in names


def test_web_search_tool_requires_query():
    out = execute_agent_tool("web_search", {})
    assert "query_required" in out


def test_workspace_tools_hidden_when_suite_disabled(monkeypatch):
    """handoff §2/§8 — workspace_* tools only advertised when WORKSPACE_SUITE_ENABLED."""
    monkeypatch.setattr(get_settings(), "workspace_suite_enabled", False)
    names = {t["name"] for t in readonly_agent_tool_schemas()}
    assert not any(n.startswith("workspace_") for n in names)
    assert "research_run" in names  # core research tool unaffected
    out = execute_agent_tool("workspace_compare", {"prompt": "compare two caches"})
    assert "workspace_suite_disabled" in out


def test_workspace_tools_advertised_when_suite_enabled(monkeypatch):
    monkeypatch.setattr(get_settings(), "workspace_suite_enabled", True)
    names = {t["name"] for t in readonly_agent_tool_schemas()}
    assert "workspace_research" in names
    assert "workspace_compare" in names
    # validation still enforced
    assert "topic_required" in execute_agent_tool("workspace_research", {"topic": "x"})
    assert "prompt_too_short" in execute_agent_tool("workspace_compare", {"prompt": "short"})


def test_agent_runtime_turn_uses_tool_loop(monkeypatch):
    monkeypatch.setattr(get_settings(), "agent_runtime_enabled", True)
    monkeypatch.setattr(get_settings(), "use_real_llm", True)
    monkeypatch.setattr(get_settings(), "anthropic_api_key", "sk-test")
    mock_loop = ToolLoopResult(
        text="| Redis | Postgres |\n|---|---|",
        provider="anthropic",
        model="claude-test",
        used_llm=True,
        tool_calls=1,
        iterations=2,
    )
    with patch("aethos_core.provider.completion.run_tool_loop_with_provider_failover", return_value=mock_loop):
        result = run_agent_runtime_turn(
            "Compare redis vs postgres in a table",
            session_id="agent-test",
        )
    assert result is not None
    assert result.used_llm is True
    assert result.tool_calls == 1
    assert result.meta.get("lane") == "agent_runtime"


def test_generative_skipped_when_agent_runtime_enabled(monkeypatch):
    monkeypatch.setattr(get_settings(), "agent_runtime_enabled", True)
    with patch("aethos_core.chat.generative_knowledge_router.route_generative_knowledge_turn") as mock_gen:
        from aethos_core.chat.chat_turn_steps import try_operational_fast_path_turn

        text = "Compare redis vs postgres capability? In table format"
        try_operational_fast_path_turn(text, session_id="gk-skip", channel="chat", emotional_context=None)
        mock_gen.assert_not_called()
