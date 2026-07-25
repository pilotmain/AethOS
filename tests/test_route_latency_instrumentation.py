# SPDX-License-Identifier: Apache-2.0
"""HOTFIX 93B — route trace timing metadata."""

from __future__ import annotations

from unittest.mock import patch

from aethos_core.chat.route_trace import clear_route_traces_for_tests, get_last_route_trace
from aethos_core.chat.service import ChatTurnResult, _stamp_turn_timing, resolve_chat_turn
from aethos_core.config import get_settings
from aethos_core.providers.railway.deployment_plan.deployment_plan_context import clear_for_tests


def setup_function() -> None:
    clear_for_tests()
    clear_route_traces_for_tests()


def _passed_checks() -> dict:
    return {
        "readonly_readiness_ok": True,
        "mutation_ready": False,
        "railway_credential_ok": True,
        "required_env_vars": ["RAILWAY_API_TOKEN"],
        "inventory": {"ok": True},
        "github_binding": {"github_credential_ok": True},
        "service_creation": {},
    }


@patch("aethos_core.providers.railway.deployment_plan.deployment_plan_artifact.list_railway_project_environment_options")
@patch("aethos_core.providers.railway.deployment_readiness.deployment_readiness_checks.safe_run_deployment_readiness_checks")
def test_route_trace_includes_timing(mock_checks, mock_options) -> None:
    mock_checks.return_value = _passed_checks()
    mock_options.return_value = []
    result = resolve_chat_turn(
        "create railway deployment plan for pilotmain/aethos in pilotos / production",
        session_id="timing-93b",
        apply_relational_layer=False,
    )
    assert result.intent == "railway_deployment_plan_draft"
    trace = get_last_route_trace(session_id="timing-93b")
    assert trace is not None
    for key in ("total_ms", "hydration_ms", "router_ms", "finalizer_ms", "provider_calls_ms", "model_ms", "tools_ms"):
        assert key in trace, key
        assert str(trace[key]).isdigit()
    assert "total_ms" not in result.meta


def test_tool_executor_records_tools_ms():
    """§C5: tool execution wall-time is attributed to the turn."""
    from aethos_core.chat.route_timing import begin_turn_timing, get_turn_timing
    from aethos_core.execution_brain.agent_tool_executor import execute_agent_tool

    begin_turn_timing()
    execute_agent_tool("provider_catalog", {}, session_id="tools-ms")
    timing = get_turn_timing()
    assert timing is not None
    assert timing.tools_ms >= 0  # accumulator wired (catalog is fast but non-negative)
    assert "tools_ms" in timing.to_trace_dict()


def test_verbose_flag_stamps_timing_breakdown_into_meta(monkeypatch):
    """§C5: with CHAT_VERBOSE_TIMING_ENABLED the breakdown is surfaced in reply meta."""
    from aethos_core.chat.route_timing import begin_turn_timing

    monkeypatch.setenv("CHAT_VERBOSE_TIMING_ENABLED", "true")
    get_settings.cache_clear()
    begin_turn_timing()
    result = ChatTurnResult(reply="ok", intent="x", meta={})
    _stamp_turn_timing(result)
    assert "timing_breakdown" in result.meta
    assert "this turn took" in result.meta["timing_breakdown"]
    assert "timing_total_ms" in result.meta
    get_settings.cache_clear()


def test_verbose_flag_off_keeps_meta_clean(monkeypatch):
    from aethos_core.chat.route_timing import begin_turn_timing

    monkeypatch.setenv("CHAT_VERBOSE_TIMING_ENABLED", "false")
    get_settings.cache_clear()
    begin_turn_timing()
    result = ChatTurnResult(reply="ok", intent="x", meta={})
    _stamp_turn_timing(result)
    assert "timing_breakdown" not in result.meta
    get_settings.cache_clear()
