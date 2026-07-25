# SPDX-License-Identifier: Apache-2.0
"""Generative knowledge routing tests."""

from __future__ import annotations

from unittest.mock import patch

from aethos_core.chat.generative_knowledge_router import (
    is_generative_knowledge_request,
    route_generative_knowledge_turn,
)
from aethos_core.provider.completion import ProviderResult
from aethos_core.provider_readonly_intent.readonly_intent_classifier import (
    classify_vercel_readonly_intent,
    extract_vercel_project_hint,
)


def test_compare_two_tools_is_generative_knowledge():
    text = "Compare redis vs postgres capability? In table format"
    assert is_generative_knowledge_request(text) is True


def test_vercel_deploy_not_generative_knowledge():
    assert is_generative_knowledge_request("redeploy killit on vercel") is False


def test_compare_routes_to_provider_not_tracked_job():
    text = "Compare redis vs postgres capability? In table format"
    mock_result = ProviderResult(
        text="| Feature | Redis | Postgres |\n|---|---|---|",
        provider="anthropic",
        model="claude-test",
        used_llm=True,
    )
    with patch(
        "aethos_core.chat.generative_knowledge_router.complete_chat",
        return_value=mock_result,
    ) as mock_chat:
        with patch("aethos_core.chat.generative_knowledge_router.provider_configured", return_value=True):
            with patch(
                "aethos_core.chat.generative_knowledge_router._raw_web_evidence_snippets",
                return_value="",
            ):
                result = route_generative_knowledge_turn(text, session_id="gk-test")
    assert result is not None
    assert result.intent == "generative_knowledge"
    assert result.used_llm is True
    assert "Redis" in result.reply
    mock_chat.assert_called_once()
    assert "Compare redis vs postgres" in mock_chat.call_args.args[0]


def test_table_format_instruction():
    from aethos_core.chat.generative_knowledge_router import _format_instruction

    assert "table" in _format_instruction("compare x vs y in a table").lower()
    assert "did not ask for a table" in _format_instruction("compare x vs y capability").lower()


def test_list_all_vercel_projects_not_scoped_to_each():
    text = "list all vercel projects and show deployment health for each"
    assert extract_vercel_project_hint(text) == ""
    intent = classify_vercel_readonly_intent(text)
    assert intent is not None
    assert intent.operation == "projects"
    assert intent.project == ""
