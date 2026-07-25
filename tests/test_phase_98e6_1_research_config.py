# SPDX-License-Identifier: Apache-2.0
"""Phase 9.8E.6.1 — Research config hydration + diagnostics."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from aethos_core.chat.service import resolve_chat_turn
from aethos_core.research.research_artifacts import clear_research_artifacts_for_tests
from aethos_core.research.research_config import (
    build_research_status,
    is_research_search_configured,
    preview_api_key,
    research_config_errors,
    validate_research_config_at_startup,
)
from aethos_core.research.research_provider import SearchResult
from aethos_core.research.providers.tavily_provider import TavilyResearchProvider


@pytest.fixture(autouse=True)
def _clean():
    clear_research_artifacts_for_tests()
    yield
    clear_research_artifacts_for_tests()


@pytest.fixture
def research_env(monkeypatch, tmp_path):
    monkeypatch.setenv("RESEARCH_ARTIFACTS_DIR", str(tmp_path / "research"))
    monkeypatch.setenv("AETHOS_BATTERIES_INCLUDED", "false")
    monkeypatch.setenv("AGENT_RUNTIME_ENABLED", "false")
    monkeypatch.setenv("USE_REAL_LLM", "false")
    monkeypatch.setenv("AUTH_ENABLED", "false")
    from aethos_core.config import get_settings

    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_preview_api_key_redacts():
    assert preview_api_key("tvly-abc123xyz789") == "tvly--****z789"


def test_research_status_incomplete_when_enabled_without_provider(research_env, monkeypatch):
    monkeypatch.setenv("WEB_RESEARCH_ENABLED", "true")
    monkeypatch.setenv("WEB_SEARCH_PROVIDER", "none")
    monkeypatch.setenv("WEB_SEARCH_API_KEY", "")
    from aethos_core.config import get_settings

    get_settings.cache_clear()
    status = build_research_status()
    assert status["enabled"] is True
    assert status["configured"] is False
    assert status["api_key_configured"] is False
    assert "WEB_SEARCH_PROVIDER is missing or none" in status["errors"]


def test_research_status_configured(research_env, monkeypatch):
    monkeypatch.setenv("WEB_RESEARCH_ENABLED", "true")
    monkeypatch.setenv("WEB_SEARCH_PROVIDER", "tavily")
    monkeypatch.setenv("WEB_SEARCH_API_KEY", "tvly-test-key-1234")
    from aethos_core.config import get_settings

    get_settings.cache_clear()
    status = build_research_status()
    assert status["configured"] is True
    assert status["provider"] == "tavily"
    assert status["api_key_configured"] is True
    assert status["api_key_preview"] == "tvly--****1234"
    assert status["errors"] == []


def test_startup_validation_logs_warning(research_env, monkeypatch, caplog):
    import logging

    monkeypatch.setenv("WEB_RESEARCH_ENABLED", "true")
    monkeypatch.setenv("WEB_SEARCH_PROVIDER", "none")
    monkeypatch.setenv("WEB_SEARCH_API_KEY", "")
    from aethos_core.config import get_settings

    get_settings.cache_clear()
    with caplog.at_level(logging.WARNING):
        validate_research_config_at_startup(get_settings())
    assert any("WEB_SEARCH_PROVIDER is missing" in r.message for r in caplog.records)


def test_research_status_api(research_env, monkeypatch):
    monkeypatch.setenv("WEB_RESEARCH_ENABLED", "true")
    monkeypatch.setenv("WEB_SEARCH_PROVIDER", "tavily")
    monkeypatch.setenv("WEB_SEARCH_API_KEY", "tvly-secret-key-9999")
    from aethos_core.config import get_settings

    get_settings.cache_clear()
    from aethos_core.api.main import app

    client = TestClient(app)
    resp = client.get("/api/v1/research/status")
    assert resp.status_code == 200
    body = resp.json()
    assert body["configured"] is True
    assert body["provider"] == "tavily"
    assert "secret" not in str(body)
    assert body["api_key_preview"].startswith("tvly-")


def test_incomplete_config_actionable_telegram_response(research_env, monkeypatch):
    monkeypatch.setenv("WEB_RESEARCH_ENABLED", "true")
    monkeypatch.setenv("WEB_SEARCH_PROVIDER", "none")
    monkeypatch.setenv("WEB_SEARCH_API_KEY", "")
    from aethos_core.config import get_settings

    get_settings.cache_clear()
    with patch("aethos_core.provider.completion.complete_chat") as mock_llm:
        result = resolve_chat_turn("Can you search the web now?", session_id="s1", channel="telegram")
    mock_llm.assert_not_called()
    assert "search provider is incomplete" in result.reply.lower()
    assert "WEB_SEARCH_PROVIDER" in result.reply
    assert "WEB_SEARCH_API_KEY" in result.reply
    assert "WEB_RESEARCH_ENABLED=true" in result.reply


def test_configured_generic_search_prompt(research_env, monkeypatch):
    monkeypatch.setenv("WEB_RESEARCH_ENABLED", "true")
    monkeypatch.setenv("WEB_SEARCH_PROVIDER", "tavily")
    monkeypatch.setenv("WEB_SEARCH_API_KEY", "tvly-test")
    from aethos_core.config import get_settings

    get_settings.cache_clear()
    result = resolve_chat_turn("Can you search the web now?", session_id="s1")
    assert "tavily" in result.reply.lower()
    assert "Tavily" in result.reply
    assert result.intent == "web_search_ready"


@patch("aethos_core.research.providers.tavily_provider.httpx.Client")
def test_tavily_provider_search(mock_client_cls, research_env):
    mock_resp = mock_client_cls.return_value.__enter__.return_value.post.return_value
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "results": [
            {"title": "Railway Docs", "url": "https://docs.railway.app/", "content": "Deploy docs"},
        ]
    }
    provider = TavilyResearchProvider("tvly-test-key")
    out = provider.search("latest Railway deployment docs", max_results=3)
    assert out.ok is True
    assert out.provider == "tavily"
    assert len(out.results) == 1
    assert out.results[0].title == "Railway Docs"


def test_real_search_prompt_uses_tavily(research_env, monkeypatch):
    monkeypatch.setenv("WEB_RESEARCH_ENABLED", "true")
    monkeypatch.setenv("WEB_SEARCH_PROVIDER", "tavily")
    monkeypatch.setenv("WEB_SEARCH_API_KEY", "tvly-test")
    from aethos_core.config import get_settings

    get_settings.cache_clear()
    fake = SearchResult(title="Railway Docs", url="https://docs.railway.app/", snippet="Deploy")
    with patch("aethos_core.research.research_runtime.retrieve_parallel") as mock_retrieve:
        from aethos_core.research.evidence_contract import normalize_search_hit

        mock_retrieve.return_value = (
            [normalize_search_hit(provider="tavily", title=fake.title, url=fake.url, snippet=fake.snippet)],
            [{"provider": "tavily", "ok": True, "count": 1}],
        )
        with patch("aethos_core.provider.completion.complete_chat") as mock_llm:
            result = resolve_chat_turn(
                "Search the web for latest Railway deployment docs",
                session_id="s1",
            )
    mock_llm.assert_not_called()
    assert result.intent == "research_synthesis"
    assert "Railway Docs" in result.reply
    assert result.meta.get("research_runtime") == "true"


def test_is_research_search_configured_helper(research_env, monkeypatch):
    monkeypatch.setenv("WEB_RESEARCH_ENABLED", "true")
    monkeypatch.setenv("WEB_SEARCH_PROVIDER", "tavily")
    monkeypatch.setenv("WEB_SEARCH_API_KEY", "tvly-x")
    from aethos_core.config import get_settings

    get_settings.cache_clear()
    assert is_research_search_configured(get_settings()) is True
    assert research_config_errors(get_settings()) == []
