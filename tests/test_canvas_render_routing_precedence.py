# SPDX-License-Identifier: Apache-2.0
"""Canvas render commands must beat informational help routing."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from aethos_core.chat.chat_turn_steps import classify_primary_intent, try_operational_fast_path_turn
from aethos_core.chat.informational_help_router import (
    compose_canvas_setup_guidance_reply,
    route_informational_help_turn,
)
from aethos_core.chat.informational_turn_classifier import (
    is_explicit_operational_tool_command,
    is_informational_help_turn,
    should_block_mutation_routing,
)
from aethos_core.config import get_settings
from aethos_core.operations.intents import infer_operation_preflight_intent


@pytest.fixture(autouse=True)
def _clean():
    from aethos_core.world_model.world_state_store import clear_world_model_for_tests

    clear_world_model_for_tests()
    yield
    clear_world_model_for_tests()


CANVAS_RENDER_PROMPTS = [
    "render a job timeline on the canvas",
    "how do I render a job timeline on the canvas?",
    "draw a status board on the canvas",
]


@pytest.mark.parametrize("prompt", CANVAS_RENDER_PROMPTS)
def test_canvas_render_not_informational_help(prompt: str):
    assert is_explicit_operational_tool_command(prompt)
    assert not is_informational_help_turn(prompt)
    assert route_informational_help_turn(prompt) is None


@pytest.mark.parametrize("prompt", CANVAS_RENDER_PROMPTS)
def test_canvas_render_primary_intent(prompt: str):
    assert classify_primary_intent(prompt) == "canvas"


def test_operational_fast_path_defers_canvas_to_agent_runtime():
    result = try_operational_fast_path_turn(
        "how do I render a job timeline on the canvas?",
        session_id="canvas-route-test",
        channel="chat",
        emotional_context=None,
    )
    assert result is None


def test_canvas_enable_question_grounded_when_enabled(monkeypatch):
    monkeypatch.setenv("CANVAS_SURFACE_ENABLED", "true")
    get_settings.cache_clear()
    reply = compose_canvas_setup_guidance_reply()
    assert "already enabled" in reply.lower()
    assert "CANVAS_SURFACE_ENABLED=true" in reply
    assert "=ON" not in reply


def test_canvas_enable_question_hosted_disabled_mentions_railway(monkeypatch):
    monkeypatch.setenv("DEPLOYMENT_MODE", "hosted")
    monkeypatch.setenv("CANVAS_SURFACE_ENABLED", "false")
    get_settings.cache_clear()
    reply = compose_canvas_setup_guidance_reply()
    assert "Railway" in reply
    assert "true" in reply
    assert ".env" not in reply


def test_how_to_enable_canvas_routes_informational_not_render():
    prompt = "how do I enable canvas?"
    assert is_informational_help_turn(prompt)
    assert not is_explicit_operational_tool_command(prompt)
    routed = route_informational_help_turn(prompt)
    assert routed is not None
    assert routed.intent == "informational_help_canvas"
    assert "enabled" in routed.reply.lower()


def test_restart_still_operational_command():
    cmd = "restart MongoDB on railway"
    assert not is_informational_help_turn(cmd)
    assert not should_block_mutation_routing(cmd)
    assert infer_operation_preflight_intent(cmd) is not None


@patch("aethos_core.chat.informational_help_router.complete_chat")
@patch("aethos_core.chat.informational_help_router.provider_configured", return_value=True)
def test_llm_help_context_includes_canvas_flag(mock_configured, mock_complete):
    from aethos_core.provider.completion import ProviderResult

    mock_complete.return_value = ProviderResult(
        text="Canvas is on.",
        provider="anthropic",
        model="test",
        used_llm=True,
    )
    route_informational_help_turn("where is the approvals panel?")
    prompt = mock_complete.call_args[0][0]
    assert "CANVAS_SURFACE_ENABLED=" in prompt
    assert "DEPLOYMENT_MODE=" in prompt
    assert "never `ON`" in prompt or "never ON" in prompt


CANVAS_PROVIDER_WORDY_PROMPTS = [
    "render a diff of killit's required vs configured env vars on the canvas",
    "render a markdown checklist of steps to finish the killit deploy on the canvas",
    "show a before/after diff of the railway env changes on the canvas",
    "render a table of my Railway projects and services on the canvas",
]


@pytest.mark.parametrize("prompt", CANVAS_PROVIDER_WORDY_PROMPTS)
def test_canvas_render_beats_provider_routing(prompt: str):
    # The verb "render" must not be matched as the render.com provider, and provider
    # keywords (railway/deploy/env) must not steal a canvas render.
    assert infer_operation_preflight_intent(prompt) is None
    assert classify_primary_intent(prompt) == "canvas"


def test_railway_canvas_diff_not_readonly_direct():
    from aethos_core.chat.railway_readonly_prompts import is_railway_readonly_direct_request

    assert (
        is_railway_readonly_direct_request(
            "show a before/after diff of the railway env changes on the canvas"
        )
        is False
    )
    # A plain railway status ask (no canvas) still routes to railway readonly.
    assert is_railway_readonly_direct_request("show railway deployment status") is True
