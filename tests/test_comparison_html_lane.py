# SPDX-License-Identifier: Apache-2.0
"""HTML comparison follow-ups and polish regression tests."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from aethos_core.chat.chat_turn_steps import classify_primary_intent
from aethos_core.chat.comparison_html_lane import comparison_html_reply, is_comparison_html_request
from aethos_core.conversation.polish_compat import polish_research_reply
from aethos_core.research.evidence_contract import normalize_search_hit
from aethos_core.research.research_session_memory import remember_research_run


# ── §B1 deterministic intent gate — the previously-misrouting prompts ────────────
# (function names carry "router" so the §End -k "router" gate collects them)


def test_intent_gate_router_classifies_command_center_orchestration():
    assert classify_primary_intent("orchestrate a team of agents to fix the failing deploy") == "orchestration"
    assert classify_primary_intent("spin up a command center to coordinate agents") == "orchestration"


def test_intent_gate_router_classifies_canvas_render():
    assert classify_primary_intent("render a job timeline to the canvas") == "canvas"
    # canvas wins over the comparison-html lane even when "comparison" is present,
    # so the html lane can no longer steal a canvas render (§B1 acceptance).
    assert classify_primary_intent("render a visual comparison table to the canvas") == "canvas"


def test_intent_gate_router_classifies_repo_review():
    assert classify_primary_intent("review my local repository for security issues") == "repo_review"
    assert classify_primary_intent("audit the codebase and explain the structure") == "repo_review"


def test_intent_gate_router_classifies_deploy():
    assert classify_primary_intent("deploy influencer-crm to railway") == "deploy"
    assert classify_primary_intent("redeploy the api service on vercel") == "deploy"


def test_intent_gate_router_is_deterministic():
    prompt = "render a job timeline to the canvas"
    labels = {classify_primary_intent(prompt) for _ in range(8)}
    assert labels == {"canvas"}, "same phrasing must map to the same primary capability every time"


def test_intent_gate_router_falls_through_for_plain_chat():
    # No keyword match → unknown, so the gate takes no action and the legacy chain runs.
    assert classify_primary_intent("hey, how are you doing today?") == "unknown"


GBRAIN_PROMPT = (
    "can you compare GBrain by Garry Tan to Kaparthay's LLM wiki idea "
    "and tell me which is best for a personal second brain"
)


def test_html_request_detected():
    assert is_comparison_html_request("can you create a simple html code for the above comparison?")
    assert is_comparison_html_request("give me a visual comparison for GBrain vs LLM wiki")


def test_polish_does_not_playground_on_compare_best():
    evidence = [
        normalize_search_hit(provider="tavily", title="GBrain", url="https://a.com", snippet="AI memory"),
    ]
    raw = "# Comparison wiki\n\nLean GBrain"
    out = polish_research_reply(
        query=GBRAIN_PROMPT,
        synthesis=object(),
        analysis=type("A", (), {"overall_confidence": 0.6, "contradictions": []})(),
        evidence=evidence,
        raw_markdown=raw,
        comparison=True,
    )
    assert "playground" not in out["reply"].lower()
    assert "Comparison wiki" in out["reply"]


@patch("aethos_core.research.comparison_html.load_comparison_context")
@patch("aethos_core.research.research_runtime.run_research_query")
def test_visual_compare_one_shot_runs_research_then_html(mock_run, mock_load, tmp_path, monkeypatch):
    monkeypatch.setenv("RESEARCH_ARTIFACTS_DIR", str(tmp_path / "research"))
    from aethos_core.config import get_settings

    get_settings.cache_clear()

    mock_run.return_value = type(
        "R",
        (),
        {
            "ok": True,
            "replay_id": "rrun-inline",
            "reply": "done",
            "intent": "research_synthesis",
        },
    )()

    class FakeCtx:
        subject_a = "GBrain by Garry Tan"
        subject_b = "Kaparthay's LLM wiki idea"
        query = GBRAIN_PROMPT
        replay_id = "rrun-inline"
        verdict = "GBrain fits agent workflows"
        lean = "GBrain by Garry Tan"
        sources = []
        evidence_a = ["Agent memory"]
        evidence_b = ["Wiki pattern"]

    mock_load.return_value = FakeCtx()

    prompt = (
        "give me a visual comparison for GBrain by Garry Tan to Kaparthay's LLM wiki idea "
        "and tell me which is best for a personal second brain"
    )
    out = comparison_html_reply(prompt, session_id="sess-new")
    assert out is not None
    body, intent, meta = out
    assert intent == "comparison_html"
    assert "```html" in body
    assert "<!DOCTYPE html>" in body
    assert "/api/v1/research/comparison-html/" in body
    assert meta.get("comparison_html_url")
    assert mock_run.called
    assert meta.get("inline_research") == "true"
    get_settings.cache_clear()


@patch("aethos_core.research.comparison_html.load_comparison_context")
def test_html_follow_up_uses_session_memory(mock_load, tmp_path, monkeypatch):
    monkeypatch.setenv("RESEARCH_ARTIFACTS_DIR", str(tmp_path / "research"))
    from aethos_core.config import get_settings

    get_settings.cache_clear()
    remember_research_run(
        session_id="sess-html",
        replay_id="rrun-abc123",
        query=GBRAIN_PROMPT,
        comparison=True,
        subjects=("GBrain by Garry Tan", "Kaparthay's LLM wiki idea"),
    )

    class FakeCtx:
        subject_a = "GBrain by Garry Tan"
        subject_b = "Kaparthay's LLM wiki idea"
        query = GBRAIN_PROMPT
        replay_id = "rrun-abc123"
        verdict = "GBrain fits agent workflows"
        lean = "GBrain by Garry Tan"
        sources = [{"title": "GBrain", "url": "https://github.com/garrytan/gbrain", "citation_id": "re-1"}]
        evidence_a = ["Agent memory layer"]
        evidence_b = ["Wiki pattern"]

    mock_load.return_value = FakeCtx()
    out = comparison_html_reply("create a simple html code for the above comparison", session_id="sess-html")
    assert out is not None
    body, intent, meta = out
    assert intent == "comparison_html"
    assert "```html" in body
    assert "<!DOCTYPE html>" in body
    assert meta.get("research_replay_id") == "rrun-abc123"
    get_settings.cache_clear()
