# SPDX-License-Identifier: Apache-2.0
"""Arbiter debate mode (Track B) + critique transparency (Track A).

Debate runs revise→re-critique rounds so the final consensus is on stress-tested
answers; the critique scorecard exposes the judgment behind the agreement %.
"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch

from aethos_core.api.routes.arbiter import _critique_scorecard
from aethos_core.arbiter import service
from aethos_core.arbiter.models import ArbiterSession, CritiqueScore, ModelResponse

_POOL = [
    {"provider": "anthropic", "model_id": "claude-x", "label": "Claude"},
    {"provider": "openrouter", "model_id": "openai/gpt-4o-mini", "label": "GPT"},
]


def _responses(tag: str):
    return [
        ModelResponse(response_id=f"r1-{tag}", provider="anthropic", model_id="claude-x", model_label="Claude", text=f"A-{tag}"),
        ModelResponse(response_id=f"r2-{tag}", provider="openrouter", model_id="openai/gpt-4o-mini", model_label="GPT", text=f"B-{tag}"),
    ]


def _critiques(responses):
    # Both critics recommend r1 → consensus on Claude.
    return [
        CritiqueScore(critic_model_id="openai/gpt-4o-mini", target_response_id=responses[0].response_id,
                      accuracy_score=0.9, completeness_score=0.9, reasoning_score=0.9, overall_score=0.9,
                      critique_text="Strong and complete.", recommended=True),
        CritiqueScore(critic_model_id="claude-x", target_response_id=responses[1].response_id,
                      accuracy_score=0.5, completeness_score=0.5, reasoning_score=0.5, overall_score=0.5,
                      critique_text="Thin in places.", recommended=False),
    ]


def _run(debate_rounds: int):
    async def fake_dispatch(pool, prompt, *, tenant_id=None):
        return _responses("d0")

    # run_critique_round is invoked once after dispatch and once per debate round.
    state = {"n": 0}

    async def fake_critique(pool, prompt, responses, *, blind=True, tenant_id=None):
        state["n"] += 1
        return _critiques(responses)

    async def fake_revise(pool, prompt, responses, critiques, *, tenant_id=None):
        return _responses(f"rev{state['n']}")

    with patch("aethos_core.arbiter.service.dispatch_to_pool", fake_dispatch), \
         patch("aethos_core.arbiter.service.run_critique_round", fake_critique), \
         patch("aethos_core.arbiter.debate_engine.run_revision_round", AsyncMock(side_effect=fake_revise)) as rev, \
         patch("aethos_core.arbiter.service.validate_pool", return_value={"valid": True, "errors": []}), \
         patch("aethos_core.arbiter.service.effective_bool", return_value=True):
        sess = asyncio.run(
            service.run_arbiter_session("a hard question", model_pool_override=_POOL, debate_rounds=debate_rounds)
        )
    return sess, rev


def test_single_pass_runs_no_debate():
    sess, rev = _run(debate_rounds=0)
    rev.assert_not_called()
    assert sess.debate_rounds == []
    assert sess.rounds_completed == 2  # dispatch + one critique


def test_debate_runs_revise_and_recritique_each_round():
    sess, rev = _run(debate_rounds=2)
    assert rev.call_count == 2  # two revise rounds
    assert len(sess.debate_rounds) == 2
    assert [r["round"] for r in sess.debate_rounds] == [1, 2]
    # dispatch(1) + initial critique(1) + 2 rounds × (revise+critique = 2) = 6
    assert sess.rounds_completed == 6
    assert sess.consensus is not None


def test_debate_rounds_are_clamped_to_max():
    # arbiter_max_debate_rounds defaults to 3 — a request for 99 must not fan out 99×.
    sess, rev = _run(debate_rounds=99)
    assert rev.call_count <= 3


def test_critique_scorecard_exposes_judgment():
    responses = _responses("x")
    sess = ArbiterSession(prompt="q", model_pool=_POOL, responses=responses, critiques=_critiques(responses))
    card = _critique_scorecard(sess)
    assert len(card) == 2
    top = card[0]
    assert top["critic"] == "GPT" and top["target"] == "Claude"  # labels, not raw ids
    assert top["recommended"] is True
    assert top["critique"] == "Strong and complete."
    assert card[0]["overall_score"] >= card[1]["overall_score"]  # sorted desc
