# SPDX-License-Identifier: Apache-2.0
"""Phase 9.8E.6 — Web intelligence lane + Telegram web-aware routing."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from aethos_core.channels.base.channel_adapter import ChannelMessage
from aethos_core.channels.inbound import handle_channel_message
from aethos_core.chat.service import resolve_chat_turn
from aethos_core.chat.web_intelligence import classify_web_intent, is_web_intelligence_request
from aethos_core.research.research_artifacts import clear_research_artifacts_for_tests, list_research_artifacts
from aethos_core.research.website_summary import extract_url_from_text, normalize_website_url
from aethos_core.runtime.authority import authority


@pytest.fixture(autouse=True)
def _clean_artifacts():
    clear_research_artifacts_for_tests()
    yield
    clear_research_artifacts_for_tests()


@pytest.fixture
def web_intel_env(monkeypatch, tmp_path):
    research_dir = tmp_path / "research_artifacts"
    monkeypatch.setenv("RESEARCH_ARTIFACTS_DIR", str(research_dir))
    monkeypatch.setenv("WEB_RESEARCH_ENABLED", "false")
    monkeypatch.setenv("WEB_SEARCH_PROVIDER", "none")
    monkeypatch.setenv("BROWSER_AUTOMATION_ENABLED", "true")
    monkeypatch.setenv("BROWSER_CAPTURE_APPROVAL_REQUIRED", "false")
    monkeypatch.setenv("CHANNEL_GATEWAY_ENABLED", "false")
    monkeypatch.setenv("AGENT_RUNTIME_ENABLED", "false")
    from aethos_core.config import get_settings

    get_settings.cache_clear()
    authority.configure_capabilities(browser_automation=True, host_executor=False, vercel_cli=False, provider_available=False)
    yield research_dir
    get_settings.cache_clear()


def _mock_capture():
    return {
        "ok": True,
        "metadata": {
            "title": "PilotOS",
            "url": "https://pilotmain.com/",
            "headings": ["h1: PilotOS", "h2: Products"],
            "visible_text_preview": "Unified product ecosystem and operating layer.",
            "links_sample": ["https://pilotmain.com/products", "https://pilotmain.com/downloads"],
            "meta_tags": [{"name": "description", "content": "PilotOS ecosystem"}],
        },
        "artifacts": [
            {"artifact_id": "bart-screenshot1", "artifact_type": "browser_screenshot"},
            {"artifact_id": "bart-meta1", "artifact_type": "deployment_metadata_only"},
        ],
    }


def test_pilotmain_normalizes_to_https():
    assert normalize_website_url("pilotmain.com") == "https://pilotmain.com"


def test_extract_url_from_website_summary_prompt():
    url = extract_url_from_text("Can you tell me high level details about pilotmain.com")
    assert url == "https://pilotmain.com"


def test_classify_website_summary_intent():
    intent = classify_web_intent("Can you tell me high level details about pilotmain.com")
    assert intent is not None
    assert intent.intent.value == "website_summary"
    assert intent.url == "https://pilotmain.com"


def test_classify_web_search_intent():
    intent = classify_web_intent("Can you search the web now")
    assert intent is not None
    assert intent.intent.value == "web_search"


def test_search_prompt_not_configured_message(web_intel_env):
    with patch("aethos_core.provider.completion.complete_chat") as mock_llm:
        result = resolve_chat_turn("Can you search the web now?", session_id="s1", channel="telegram")
    mock_llm.assert_not_called()
    assert "Web research is disabled" in result.reply
    assert result.meta.get("lane") == "web_intelligence"
    assert result.used_llm is False
    arts = list_research_artifacts()
    assert not any(a["artifact_type"] == "web_search_result_set" for a in arts)


@patch("aethos_core.browser.runtime.browser_runtime.run_browser_evidence_capture", return_value=_mock_capture())
def test_website_summary_creates_artifact(mock_capture, web_intel_env):
    with patch("aethos_core.provider.completion.complete_chat") as mock_llm:
        result = resolve_chat_turn(
            "Can you tell me high level details about pilotmain.com",
            session_id="s1",
            channel="chat",
        )
    mock_llm.assert_not_called()
    mock_capture.assert_called_once()
    assert "browser evidence" in result.reply.lower()
    assert "pilotmain.com" in result.reply.lower()
    assert result.intent == "website_summary"
    assert result.meta.get("web_intelligence") == "true"
    arts = list_research_artifacts()
    assert any(a["artifact_type"] == "website_metadata_summary" for a in arts)


@patch("aethos_core.browser.runtime.browser_runtime.run_browser_evidence_capture", return_value=_mock_capture())
def test_telegram_parity_same_lane(mock_capture, web_intel_env):
    msg = ChannelMessage(
        channel="telegram",
        text="Can you tell me high level details about pilotmain.com",
        session_id="tg-1",
        external_chat_id="123",
        external_user_id="456",
    )
    with patch("aethos_core.channels.inbound._maybe_pairing_gate", return_value=None):
        with patch("aethos_core.provider.completion.complete_chat") as mock_llm:
            turn = handle_channel_message(msg)
    mock_llm.assert_not_called()
    assert turn.ok
    assert turn.intent == "website_summary"
    assert "browser evidence" in turn.reply.lower()


@patch(
    "aethos_core.browser.runtime.browser_runtime.run_browser_evidence_capture",
    return_value={"ok": False, "error": "DNS resolution failed", "failure_class": "network_error"},
)
def test_browser_error_honest_failure(mock_capture, web_intel_env):
    result = resolve_chat_turn("inspect pilotmain.com", session_id="s1")
    assert "could not reach" in result.reply.lower()
    assert "DNS" in result.reply or "network" in result.reply.lower()
    assert result.used_llm is False


def test_browser_disabled_no_generic_denial(web_intel_env, monkeypatch):
    monkeypatch.setenv("BROWSER_AUTOMATION_ENABLED", "false")
    from aethos_core.config import get_settings

    get_settings.cache_clear()
    authority.configure_capabilities(browser_automation=False, host_executor=False, vercel_cli=False, provider_available=False)
    with patch("aethos_core.provider.completion.complete_chat") as mock_llm:
        result = resolve_chat_turn("Can you tell me high level details about pilotmain.com", session_id="s1")
    mock_llm.assert_not_called()
    assert "Browser automation is disabled" in result.reply
    assert "I don't have live web access" not in result.reply


def test_web_intelligence_not_generic_fallback(web_intel_env):
    with patch("aethos_core.provider.completion.complete_chat") as mock_llm:
        mock_llm.return_value.text = "I don't have live web access."
        mock_llm.return_value.used_llm = True
        result = resolve_chat_turn("Can you search the web now?", session_id="s1")
    assert "disabled" in result.reply.lower() or "not configured" in result.reply.lower()
    assert result.reply != "I don't have live web access."


def test_policy_blocks_login_automation(web_intel_env):
    assert is_web_intelligence_request("login to pilotmain.com and fill out the form")
    result = resolve_chat_turn("login to pilotmain.com and fill out the form", session_id="s1")
    assert "policy denial" in result.reply.lower() or "blocked" in result.reply.lower()
    assert result.intent == "web_intelligence_policy_denial"


def test_inspect_prompt_routes_web_intelligence_not_browser_job(web_intel_env):
    """Website inspection should use sync web intelligence, not async browser evidence job."""
    with patch("aethos_core.chat.browser_evidence_prompts.create_browser_evidence_job_reply") as job:
        job.return_value = None
        with patch(
            "aethos_core.browser.runtime.browser_runtime.run_browser_evidence_capture",
            return_value=_mock_capture(),
        ):
            result = resolve_chat_turn("inspect pilotmain.com", session_id="s1")
    job.assert_called_once()
    assert result.intent == "website_summary"
