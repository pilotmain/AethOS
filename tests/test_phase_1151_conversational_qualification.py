# SPDX-License-Identifier: Apache-2.0
"""Phase 11.5.1 — Production conversational qualification tests."""

from __future__ import annotations

from aethos_core.conversation.legacy_polish_api import assess_conversational_reliability
from aethos_core.conversation.legacy_polish_api import assess_qualification_dimensions
from aethos_core.conversation.legacy_polish_api import assess_production_conversational_qualification
from aethos_core.conversation.legacy_polish_api import assess_trust_integrity_qualification
from aethos_core.conversation.legacy_polish_api import ensure_reliable_response
from aethos_core.operational_truth.capability_truth_matrix import build_capability_truth_matrix


def _evidence() -> list[dict]:
    return [
        {"title": "Clemyjontri Park — McLean, VA", "snippet": "Accessible playground with multiple play zones.", "confidence": 0.88, "provider": "tavily"},
        {"title": "Kids Cove — Vienna, VA", "snippet": "Excellent for younger children with shaded seating.", "confidence": 0.82, "provider": "tavily"},
        {"title": "Ashburn Park — Ashburn, VA", "snippet": "Dinosaur-themed playground for younger children.", "confidence": 0.79, "provider": "tavily"},
        {"title": "Lee District Park — Alexandria, VA", "snippet": "Sprayground for NOVA families.", "confidence": 0.76, "provider": "tavily"},
        {"title": "Bryant Park — Fairfax, VA", "snippet": "Shaded climbing playground.", "confidence": 0.71, "provider": "tavily"},
        {"title": "Occoquan Park — Lorton, VA", "snippet": "Waterfront playground.", "confidence": 0.68, "provider": "tavily"},
        {"title": "Kids Cove — Vienna, VA", "snippet": "dup", "confidence": 0.5, "provider": "web"},
    ]


def test_production_conversational_qualification():
    state = assess_production_conversational_qualification()
    assert state["phase"] == "11.5.1"
    assert state["production_qualified"] is True
    assert state["qualification_tier"] == "production conversational"
    assert state["sample"]["contract"]["result_count"] == 5
    assert len(state["sample"]["items"]) == 5
    assert "0.62" not in state["sample"]["reply"]
    assert state["qualification"]["passed_count"] >= 7


def test_qualification_dimensions():
    reliability = ensure_reliable_response(
        query="top five rated playgrounds in Virginia",
        evidence=_evidence(),
        overall_confidence=0.72,
        include_followups=True,
    )
    dims = assess_qualification_dimensions(reliability=reliability)
    assert dims["qualified"] is True
    assert dims["dimensions"]["intent_fidelity"]["passed"] is True
    assert dims["dimensions"]["machinery_suppression"]["passed"] is True


def test_trust_integrity_qualification():
    reliability = ensure_reliable_response(
        query="top five rated playgrounds in Virginia",
        evidence=_evidence(),
        overall_confidence=0.72,
    )
    trust = assess_trust_integrity_qualification(reliability=reliability)
    assert trust["trust_integrity_ok"] is True
    assert trust["human_readable"] is True


def test_conversational_reliability_aggregate_1151():
    state = assess_conversational_reliability()
    assert state["phase"] == "11.5.1"
    assert state["verified"] is True
    assert len(state["sample"]["items"]) == 5


def test_capability_matrix_conversational_qualification():
    matrix = build_capability_truth_matrix()
    qual = next((r for r in matrix if r.get("id") == "conversational_qualification"), None)
    assert qual is not None and qual["verification_coverage_pct"] >= 90
