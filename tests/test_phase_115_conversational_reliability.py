# SPDX-License-Identifier: Apache-2.0
"""Phase 11.5 — Conversational reliability tests."""

from __future__ import annotations

from aethos_core.conversation.legacy_polish_api import list_conversational_scenarios
from aethos_core.conversation.legacy_polish_api import assess_conversational_reliability
from aethos_core.conversation.legacy_polish_api import ensure_reliable_response
from aethos_core.human_trust_language.confidence_translation import translate_confidence
from aethos_core.intent_reliability.constraint_runtime import enforce_constraints
from aethos_core.intent_reliability.intent_contracts import parse_intent_contract
from aethos_core.operational_truth.capability_truth_matrix import build_capability_truth_matrix
from aethos_core.presentation_integrity.conversational_cleanroom import cleanroom_output


def _evidence() -> list[dict]:
    return [
        {"title": "Kids Cove — Vienna, VA", "snippet": "Excellent toddler sections, shaded seating.", "confidence": 0.82, "provider": "tavily"},
        {"title": "Ashburn Park — Ashburn, VA", "snippet": "Dinosaur-themed playground for younger children.", "confidence": 0.79, "provider": "tavily"},
        {"title": "Clemyjontri Park — McLean, VA", "snippet": "Accessible playground with diverse play zones.", "confidence": 0.88, "provider": "tavily"},
        {"title": "Lee District Park — Alexandria, VA", "snippet": "Sprayground for NOVA families.", "confidence": 0.76, "provider": "tavily"},
        {"title": "Bryant Park — Fairfax, VA", "snippet": "Shaded climbing playground.", "confidence": 0.71, "provider": "tavily"},
        {"title": "Occoquan Park — Lorton, VA", "snippet": "Waterfront playground.", "confidence": 0.68, "provider": "tavily"},
        {"title": "Kids Cove — Vienna, VA", "snippet": "dup", "confidence": 0.5, "provider": "web"},
    ]


def test_ensure_reliable_response_top_five():
    result = ensure_reliable_response(
        query="top five rated playgrounds in Virginia",
        evidence=_evidence(),
        overall_confidence=0.72,
        include_followups=True,
    )
    assert result["ok"] is True
    assert result["phase"] == "11.5"
    assert result["contract"]["result_count"] == 5
    assert len(result["items"]) == 5
    assert "0.62" not in result["reply"]
    assert "re-" not in result["reply"]
    assert "rrun-" not in result["reply"]


def test_confidence_translation_casual():
    phrase = translate_confidence(score=0.62, query="playgrounds in Virginia", mode="casual")
    assert "0.62" not in phrase
    assert "consistently appeared" in phrase.lower() or "sources" in phrase.lower()


def test_confidence_translation_engineering():
    phrase = translate_confidence(score=0.62, mode="engineering")
    assert "0.62" in phrase


def test_intent_enforcement():
    contract = parse_intent_contract("top five playgrounds in Virginia")
    items = [{"name": f"p{i}", "score": 0.8 - i * 0.05} for i in range(7)]
    enforced = enforce_constraints(contract=contract, items=items)
    assert enforced["validation"]["expected_count"] == 5
    assert len(enforced["items"]) == 5


def test_cleanroom_suppresses_telemetry():
    raw = "Overall confidence: medium / 0.62\nFreshness: 0.45\n[re-abc12345]"
    cleaned = cleanroom_output(raw, mode="casual")
    assert "0.62" not in cleaned
    assert "0.45" not in cleaned
    assert "re-abc12345" not in cleaned


def test_conversational_harness_v2():
    scenarios = list_conversational_scenarios()
    assert len(scenarios) == 8
    assert all(s["harness_version"] == "2.0" for s in scenarios)


def test_conversational_reliability_aggregate():
    state = assess_conversational_reliability()
    assert state["phase"] == "11.5.1"
    assert state["verified"] is True
    assert state["production_qualified"] is True
    assert len(state["sample"]["items"]) == 5


def test_capability_matrix_conversational_reliability():
    matrix = build_capability_truth_matrix()
    rel = next((r for r in matrix if r.get("id") == "conversational_reliability"), None)
    assert rel is not None and rel["verification_coverage_pct"] >= 88
