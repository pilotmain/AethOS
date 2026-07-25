# SPDX-License-Identifier: Apache-2.0
"""Comparison research routing and wiki synthesis."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from aethos_core.chat.web_intelligence import classify_web_intent, is_comparison_research_request, is_web_intelligence_request
from aethos_core.research.confidence_engine import analyze_evidence
from aethos_core.research.evidence_contract import ResearchEvidenceItem, normalize_search_hit
from aethos_core.research.planner import ResearchMode, extract_comparison_subjects, plan_research
from aethos_core.research.synthesis_engine import format_comparison_wiki_markdown, synthesize_comparison_research


GBRAIN_PROMPT = (
    "can you compare GBrain by Garry Tan to Kaparthay's LLM wiki idea "
    "and tell me which is best for a personal second brain"
)


def test_comparison_prompt_detected():
    assert is_comparison_research_request(GBRAIN_PROMPT)
    assert is_web_intelligence_request(GBRAIN_PROMPT)
    intent = classify_web_intent(GBRAIN_PROMPT)
    assert intent is not None
    assert intent.query


def test_extract_comparison_subjects():
    pair = extract_comparison_subjects(GBRAIN_PROMPT)
    assert pair is not None
    assert "GBrain" in pair[0]
    assert "wiki" in pair[1].lower()


def test_planner_deep_synthesis_with_queries():
    plan = plan_research(GBRAIN_PROMPT, max_results=8)
    assert plan.mode == ResearchMode.DEEP_SYNTHESIS
    assert plan.comparison_subjects is not None
    assert len(plan.search_queries) >= 3


def test_comparison_wiki_markdown_has_verdict():
    evidence = [
        normalize_search_hit(provider="tavily", title="GBrain second brain", url="https://a.com", snippet="Personal AI memory assistant"),
        normalize_search_hit(provider="tavily", title="LLM wiki notes", url="https://b.com", snippet="Knowledge wiki for LLM reference"),
    ]
    analysis = analyze_evidence(evidence)
    subjects = extract_comparison_subjects(GBRAIN_PROMPT)
    assert subjects
    synthesis = synthesize_comparison_research(GBRAIN_PROMPT, subjects[0], subjects[1], evidence, analysis)
    md = format_comparison_wiki_markdown(
        query=GBRAIN_PROMPT,
        subject_a=subjects[0],
        subject_b=subjects[1],
        synthesis=synthesis,
        analysis=analysis,
        evidence=evidence,
        replay_id="rrun-test",
    )
    assert "Comparison wiki" in md
    assert "Side by side" in md
    assert "Verdict" in md
    assert "Mission Control → Research" in md


@patch("aethos_core.research.research_runtime.retrieve_parallel")
def test_chat_routes_comparison_to_research_runtime(mock_retrieve, monkeypatch, tmp_path):
    monkeypatch.setenv("RESEARCH_ARTIFACTS_DIR", str(tmp_path / "research"))
    monkeypatch.setenv("WEB_RESEARCH_ENABLED", "true")
    monkeypatch.setenv("WEB_SEARCH_PROVIDER", "tavily")
    monkeypatch.setenv("WEB_SEARCH_API_KEY", "tvly-test")
    from aethos_core.config import get_settings
    from aethos_core.research.research_artifacts import clear_research_artifacts_for_tests
    from aethos_core.chat.service import resolve_chat_turn

    get_settings.cache_clear()
    clear_research_artifacts_for_tests()

    item = normalize_search_hit(provider="tavily", title="GBrain", url="https://a.com", snippet="AI second brain tool")
    mock_retrieve.return_value = ([item], [{"provider": "tavily", "ok": True, "count": 1}])

    out = resolve_chat_turn(GBRAIN_PROMPT, session_id="research-test")
    assert out.meta.get("research_runtime") == "true"
    assert out.meta.get("comparison") == "true"
    assert "Comparison wiki" in out.reply or "Research" in out.reply

    clear_research_artifacts_for_tests()
    get_settings.cache_clear()
