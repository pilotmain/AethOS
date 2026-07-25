# SPDX-License-Identifier: Apache-2.0
"""The generative team-planning handler produces a real per-role deliverable + a contract.

This locks the fix for the "only Operations Analyst shows / qa_verification — no handler"
regression: every named role now routes to _run_planning, emits an LLM-backed plan slice, and
sets a contract so it renders in the report's ## Agents section.
"""

from __future__ import annotations

import types

import aethos_core.provider.completion as completion
from aethos_core.agents.runtime.agent_context import AgentContext
from aethos_core.agents.runtime.delegation import _run_planning, _run_substrate


def _fake_completion(monkeypatch, text="- Define schema\n- Choose framework"):
    monkeypatch.setattr(completion, "provider_configured", lambda: True)
    monkeypatch.setattr(
        completion,
        "complete_chat",
        lambda *a, **k: types.SimpleNamespace(text=text, used_llm=True),
    )


def _ctx(agent_id="qa_verification", task="qa: test strategy"):
    return AgentContext(
        agent_id=agent_id, task=task, action="team_planning",
        session_id="t", user_request="build a URL shortener",
    )


def test_planning_handler_emits_body_and_contract(monkeypatch):
    _fake_completion(monkeypatch)
    body, summary, evidence, extra = _run_planning(_ctx(), {})
    assert "test strategy" in body.lower()
    assert "Define schema" in body
    contract = extra.get("contract")
    assert contract and contract["status"] == "completed"
    assert contract["agent_id"] == "qa_verification"
    assert contract["findings"]  # non-empty so the role shows in the report


def test_qa_verification_routes_through_substrate_not_no_handler(monkeypatch):
    # The old bug: qa_verification fell through _run_substrate → "no handler" artifact.
    _fake_completion(monkeypatch)
    body, summary, evidence, extra = _run_substrate(_ctx("qa_verification", "qa: test strategy"))
    assert "no handler" not in body.lower()
    assert extra.get("contract") is not None


def test_planning_blocked_without_provider(monkeypatch):
    monkeypatch.setattr(completion, "provider_configured", lambda: False)
    body, summary, evidence, extra = _run_planning(_ctx(), {})
    assert extra["contract"]["status"] == "blocked"
