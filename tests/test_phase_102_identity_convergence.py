# SPDX-License-Identifier: Apache-2.0
"""Phase 10.2 — Identity convergence tests."""

from __future__ import annotations

from aethos_core.chat.handlers import capability_matrix_reply, greeting_reply, identity_reply
from aethos_core.identity.governance_presence import governance_visibility
from aethos_core.identity.introduction_engine import who_are_you_reply
from aethos_core.identity.response_alignment import align_legacy_phrasing
from aethos_core.relational.warmth_engine import apply_warmth


def test_greeting_is_warm_and_not_tool_oriented():
    reply = greeting_reply("hi")
    assert "try a capability" not in reply.lower()
    assert any(
        phrase in reply.lower()
        for phrase in (
            "aethos",
            "what are we focusing on",
            "work through",
            "most important thing",
            "i'm here",
        )
    )


def test_who_are_you_introduces_operational_intelligence():
    reply = who_are_you_reply()
    assert "governed operational intelligence" in reply.lower()
    assert "host executor" not in reply.lower()
    assert "browser automation:" not in reply.lower()
    assert "trustworthy operational partnership" in reply.lower()


def test_identity_reply_matches_who_are_you():
    assert identity_reply() == who_are_you_reply()


def test_capability_overview_is_human_centered():
    reply = capability_matrix_reply()
    assert "this build" not in reply.lower()
    assert "lane b" not in reply.lower()
    assert "deterministic answers" not in reply.lower()
    assert "how i can help" in reply.lower()


def test_legacy_phrasing_alignment():
    raw = "Host executor: **off** — try a capability question in this build."
    aligned = align_legacy_phrasing(raw)
    assert "host executor" not in aligned.lower()
    assert "this build" not in aligned.lower()
    assert "try a capability question" not in aligned.lower()


def test_greeting_suppresses_governance_footer():
    shaped = apply_warmth(
        greeting_reply("hi"),
        emotional_context={"mode": {"mode": "companion"}, "signals": {}},
        intent="greeting",
    )
    assert "Governed assistance — I recommend" not in shaped
    assert "approval-gated" not in shaped


def test_mutation_preflight_gets_strong_governance_visibility():
    assert governance_visibility(intent="mutation_preflight") == "strong"


def test_capability_question_has_implicit_governance():
    assert governance_visibility(intent="capability_question") == "implicit"
