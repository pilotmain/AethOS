# SPDX-License-Identifier: Apache-2.0
"""Phase 11.4 — Human research synthesis & conversational intelligence tests."""

from __future__ import annotations

from aethos_core.conversation.legacy_polish_api import assess_conversational_intelligence
from aethos_core.conversation.intent_contracts import parse_intent_contract
from aethos_core.conversation.polish_compat import polish_chat_reply, synthesize_human_response
from aethos_core.human_trust.confidence_restraint import should_show_telemetry
from aethos_core.operational_truth.capability_truth_matrix import build_capability_truth_matrix
from aethos_core.presentation_safety.artifact_suppression import suppress_artifacts
from aethos_core.synthesis_harness.scenarios import list_synthesis_scenarios


def _playground_evidence() -> list[dict]:
    return [
        {"title": "Kids Cove — Vienna, VA", "snippet": "Excellent for younger children, shaded seating.", "confidence": 0.82, "provider": "tavily"},
        {"title": "Ashburn Park — Ashburn, VA", "snippet": "Dinosaur-themed playground with toddler sections.", "confidence": 0.79, "provider": "tavily"},
        {"title": "Clemyjontri Park — McLean, VA", "snippet": "Accessible playground with diverse play zones.", "confidence": 0.88, "provider": "tavily"},
        {"title": "Lee District Park — Alexandria, VA", "snippet": "Sprayground popular with NOVA families.", "confidence": 0.76, "provider": "tavily"},
        {"title": "Bryant Park — Fairfax, VA", "snippet": "Shaded playground with climbing structures.", "confidence": 0.71, "provider": "tavily"},
        {"title": "Occoquan Park — Lorton, VA", "snippet": "Waterfront playground.", "confidence": 0.68, "provider": "tavily"},
        {"title": "Kids Cove — Vienna, VA", "snippet": "Duplicate", "confidence": 0.5, "provider": "web"},
    ]


def test_intent_contract_top_five():
    contract = parse_intent_contract("top five rated playgrounds in Virginia")
    assert contract.result_count == 5
    assert contract.ranked is True
    assert contract.geographic_filter == "Virginia"


def test_synthesis_exactly_five_results():
    result = synthesize_human_response(
        query="top five rated playgrounds in Virginia",
        evidence=_playground_evidence(),
        overall_confidence=0.72,
        include_followups=True,
    )
    assert result["ok"] is True
    assert result["contract"]["result_count"] == 5
    assert len(result["items"]) == 5
    assert "re-" not in result["reply"].lower()
    assert "rrun-" not in result["reply"]
    assert "0.62" not in result["reply"]
    assert "Overall confidence" not in result["reply"]
    assert "## Artifacts" not in result["reply"]


def test_artifact_suppression():
    raw = "Great park [re-4fa760f6]. Replay: rrun-b9b184108d64\n## Artifacts\n- rart-1315de31a637"
    cleaned = suppress_artifacts(raw, mode="casual")
    assert "re-4fa760f6" not in cleaned
    assert "rrun-" not in cleaned
    assert "rart-" not in cleaned
    assert "## Artifacts" not in cleaned


def test_confidence_restraint_casual_mode():
    assert should_show_telemetry(mode="casual") is False
    assert should_show_telemetry(mode="engineering") is True


def test_polish_chat_reply_strips_internals():
    raw = "Answer here [re-abc12345]. Overall confidence: medium / 0.62"
    polished = polish_chat_reply(reply=raw, mode="casual")
    assert "re-abc12345" not in polished
    assert "0.62" not in polished


def test_synthesis_harness_scenarios():
    scenarios = list_synthesis_scenarios()
    assert len(scenarios) == 8
    assert any(s["id"] == "top_5_request" for s in scenarios)


def test_conversational_intelligence_aggregate():
    state = assess_conversational_intelligence()
    assert state["phase"] == "11.4"
    assert state["sample_synthesis"]["verified"] is True
    assert len(state["sample_synthesis"]["items"]) == 5


def test_capability_matrix_synthesis_baselines():
    matrix = build_capability_truth_matrix()
    synth = next((r for r in matrix if r.get("id") == "conversational_synthesis"), None)
    safety = next((r for r in matrix if r.get("id") == "presentation_safety"), None)
    assert synth is not None and synth["verification_coverage_pct"] >= 84
    assert safety is not None and safety["verification_coverage_pct"] >= 90
