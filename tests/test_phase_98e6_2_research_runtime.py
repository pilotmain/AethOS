# SPDX-License-Identifier: Apache-2.0
"""Phase 9.8E.6.2 — Universal research intelligence runtime."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from aethos_core.chat.service import resolve_chat_turn
from aethos_core.research.confidence_engine import analyze_evidence
from aethos_core.research.evidence_contract import ResearchEvidenceItem, normalize_search_hit
from aethos_core.research.planner import ResearchMode, plan_research
from aethos_core.research.research_artifacts import clear_research_artifacts_for_tests, list_research_artifacts
from aethos_core.research.research_runtime import get_research_replay, run_research_query
from aethos_core.research.synthesis_engine import synthesize_research


@pytest.fixture(autouse=True)
def _clean():
    clear_research_artifacts_for_tests()
    yield
    clear_research_artifacts_for_tests()


@pytest.fixture
def research_env(monkeypatch, tmp_path):
    monkeypatch.setenv("RESEARCH_ARTIFACTS_DIR", str(tmp_path / "research"))
    monkeypatch.setenv("WEB_RESEARCH_ENABLED", "true")
    monkeypatch.setenv("WEB_SEARCH_PROVIDER", "tavily")
    monkeypatch.setenv("WEB_SEARCH_API_KEY", "tvly-test")
    monkeypatch.setenv("BROWSER_AUTOMATION_ENABLED", "false")
    from aethos_core.config import get_settings

    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def _evidence(title: str, url: str, snippet: str, *, cite: str = "re-a") -> ResearchEvidenceItem:
    item = normalize_search_hit(provider="tavily", title=title, url=url, snippet=snippet)
    item.citation_id = cite
    return item


def test_planner_operational_mode():
    plan = plan_research("Search latest Railway deployment rollback guidance")
    assert plan.mode == ResearchMode.OPERATIONAL
    assert "tavily" in plan.providers
    assert plan.browser_verification is True


def test_planner_technical_mode():
    plan = plan_research("Research Next.js 16 migration risks")
    assert plan.mode == ResearchMode.TECHNICAL


def test_confidence_contradiction_detection():
    items = [
        _evidence("A", "https://a.com", "Endpoint X is deprecated now", cite="re-a"),
        _evidence("B", "https://b.com", "Endpoint X is still active and supported", cite="re-b"),
    ]
    analysis = analyze_evidence(items)
    assert analysis.contradictions
    assert analysis.overall_confidence < 0.7


def test_synthesis_references_citations():
    items = [_evidence("Railway Docs", "https://docs.railway.app/", "Rollback via deployment history", cite="re-1")]
    analysis = analyze_evidence(items)
    synth = synthesize_research("Railway rollback guidance", items, analysis)
    assert "re-1" in synth.citations
    assert synth.bullets


@patch("aethos_core.research.research_runtime.retrieve_parallel")
def test_research_runtime_creates_artifacts(mock_retrieve, research_env):
    mock_retrieve.return_value = (
        [_evidence("Railway rollback", "https://docs.railway.app/deploy/rollback", "Use rollback in dashboard")],
        [{"provider": "tavily", "ok": True, "count": 1}],
    )
    result = run_research_query("Search latest Railway deployment rollback guidance", channel="chat")
    assert result.ok
    assert result.replay_id.startswith("rrun-")
    types = {a["artifact_type"] for a in list_research_artifacts(limit=20)}
    assert "research_query" in types
    assert "research_result_set" in types
    assert "research_synthesis" in types
    assert "research_confidence_analysis" in types
    assert "research_replay" in types
    assert "Research synthesis" in result.reply


@patch("aethos_core.research.research_runtime.retrieve_parallel")
def test_chat_routes_through_research_runtime(mock_retrieve, research_env):
    mock_retrieve.return_value = (
        [_evidence("GH Actions cache", "https://docs.github.com/actions", "Cache v4 updates")],
        [{"provider": "tavily", "ok": True, "count": 1}],
    )
    with patch("aethos_core.provider.completion.complete_chat") as mock_llm:
        out = resolve_chat_turn("Research latest GitHub Actions caching changes", session_id="s1")
    mock_llm.assert_not_called()
    assert out.meta.get("research_runtime") == "true"
    assert "Research synthesis" in out.reply


@patch("aethos_core.research.research_runtime.retrieve_parallel")
def test_research_replay_api(mock_retrieve, research_env):
    mock_retrieve.return_value = (
        [_evidence("Doc", "https://example.com", "snippet")],
        [{"provider": "tavily", "ok": True, "count": 1}],
    )
    result = run_research_query("Research Next.js 16 migration risks", channel="api")
    replay = get_research_replay(result.replay_id)
    assert replay is not None
    assert replay.get("artifact_type") == "research_replay"

    from aethos_core.api.main import app

    client = TestClient(app)
    resp = client.get(f"/api/v1/research/replay/{result.replay_id}")
    assert resp.status_code == 200
    assert resp.json()["replay"]["artifact_id"] == result.replay_id


@patch("aethos_core.research.research_runtime.retrieve_parallel")
def test_post_research_query_api(mock_retrieve, research_env):
    mock_retrieve.return_value = ([], [])
    from aethos_core.api.main import app

    client = TestClient(app)
    resp = client.post(
        "/api/v1/research/query",
        json={"message": "Research Next.js 16 migration risks", "session_id": "api"},
    )
    assert resp.status_code == 200
    assert resp.json().get("replay_id", "").startswith("rrun-")


def test_research_providers_api(research_env):
    from aethos_core.api.main import app

    client = TestClient(app)
    resp = client.get("/api/v1/research/providers")
    assert resp.status_code == 200
    ids = {p["provider_id"] for p in resp.json()["providers"]}
    assert "tavily" in ids
