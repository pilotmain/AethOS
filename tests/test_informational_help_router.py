# SPDX-License-Identifier: Apache-2.0
"""Informational how-to routing — real answers, not canned blurbs."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from aethos_core.chat.front_door_intent import classify_front_door_intent, compose_front_door_reply
from aethos_core.chat.informational_help_router import (
    compose_local_workspace_setup_reply,
    is_canned_general_help_blurb,
    route_informational_help_turn,
)
from aethos_core.chat.informational_turn_classifier import should_block_mutation_routing
from aethos_core.config import get_settings
from aethos_core.operations.intents import infer_operation_preflight_intent


@pytest.fixture(autouse=True)
def _clean_world_model():
    from aethos_core.world_model.world_state_store import clear_world_model_for_tests

    clear_world_model_for_tests()
    yield
    clear_world_model_for_tests()


def test_vague_help_returns_canned_blurb():
    result = route_informational_help_turn("help")
    assert result is not None
    assert result.intent == "general_help"
    assert is_canned_general_help_blurb(result.reply)


def test_local_workspace_question_not_canned_blurb_hosted(monkeypatch):
    monkeypatch.setenv("DEPLOYMENT_MODE", "hosted")
    get_settings.cache_clear()

    result = route_informational_help_turn("where do I add a local workspace path?")
    assert result is not None
    assert result.intent == "informational_help_local_workspace"
    assert not is_canned_general_help_blurb(result.reply)
    assert "GitHub" in result.reply
    assert "Code workspaces" in result.reply
    assert "laptop" in result.reply.lower()


def test_local_workspace_question_local_mode(monkeypatch):
    monkeypatch.setenv("DEPLOYMENT_MODE", "local")
    get_settings.cache_clear()

    reply = compose_local_workspace_setup_reply()
    assert "Local Workspaces" in reply
    assert "absolute path" in reply.lower()
    assert "GitHub" not in reply


def test_openai_key_question_specific_answer():
    result = route_informational_help_turn("where do I add my OpenAI key?")
    assert result is not None
    assert result.intent == "informational_help_provider_credentials"
    assert "Providers" in result.reply
    assert not is_canned_general_help_blurb(result.reply)


def test_channel_connect_question_specific_answer():
    result = route_informational_help_turn("how do I connect a channel?")
    assert result is not None
    assert result.intent == "informational_help_channels"
    assert "Integrations" in result.reply
    assert not is_canned_general_help_blurb(result.reply)


def test_how_to_blocks_mutation_not_preflight():
    question = "where do I add a local workspace path?"
    assert should_block_mutation_routing(question)
    assert infer_operation_preflight_intent(question) is None


def test_explicit_restart_still_operational_command():
    command = "restart MongoDB on railway"
    assert not should_block_mutation_routing(command)
    assert classify_front_door_intent(command) == "mutation_request"


@patch("aethos_core.chat.informational_help_router.complete_chat")
@patch("aethos_core.chat.informational_help_router.provider_configured", return_value=True)
def test_specific_question_can_use_llm(mock_configured, mock_complete):
    from aethos_core.provider.completion import ProviderResult

    mock_complete.return_value = ProviderResult(
        text="Open Mission Control → Workspaces → Calendar to add local events.",
        provider="anthropic",
        model="claude-test",
        used_llm=True,
    )
    result = route_informational_help_turn("where do I add calendar events in the UI?")
    assert result is not None
    assert result.intent == "informational_help"
    assert result.used_llm is True
    assert not is_canned_general_help_blurb(result.reply)
    mock_complete.assert_called_once()


def test_front_door_general_help_delegates_to_router():
    composed = compose_front_door_reply(
        "general_help",
        text="where do I add my OpenAI key?",
    )
    assert composed is not None
    body, intent, _ = composed
    assert intent == "informational_help_provider_credentials"
    assert "Providers" in body
    assert not is_canned_general_help_blurb(body)
