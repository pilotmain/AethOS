# SPDX-License-Identifier: Apache-2.0
"""Phase 11.4.1 — Conversational convergence tests."""

from __future__ import annotations

from aethos_core.conversation.legacy_polish_api import describe_interaction_layers, resolve_surface
from aethos_core.conversation.legacy_polish_api import build_maturity_profile
from aethos_core.conversation.legacy_polish_api import assess_production_interaction
from aethos_core.conversation.legacy_polish_api import assess_conversational_convergence
from aethos_core.conversation.legacy_polish_api import validate_surface_integrity
from aethos_core.conversation.legacy_polish_api import assess_trust_maturity
from aethos_core.conversation.legacy_polish_api import harness_state
from aethos_core.conversation.legacy_polish_api import ensure_reliable_response
from aethos_core.operational_truth.capability_truth_matrix import build_capability_truth_matrix


def _evidence() -> list[dict]:
    return [
        {"title": "Kids Cove — Vienna, VA", "snippet": "Excellent for younger children, shaded seating.", "confidence": 0.82, "provider": "tavily"},
        {"title": "Ashburn Park — Ashburn, VA", "snippet": "Dinosaur-themed playground for younger children.", "confidence": 0.79, "provider": "tavily"},
        {"title": "Clemyjontri Park — McLean, VA", "snippet": "Accessible playground with diverse play zones.", "confidence": 0.88, "provider": "tavily"},
        {"title": "Lee District Park — Alexandria, VA", "snippet": "Sprayground for NOVA families.", "confidence": 0.76, "provider": "tavily"},
        {"title": "Bryant Park — Fairfax, VA", "snippet": "Shaded climbing playground.", "confidence": 0.71, "provider": "tavily"},
        {"title": "Occoquan Park — Lorton, VA", "snippet": "Waterfront playground.", "confidence": 0.68, "provider": "tavily"},
        {"title": "Kids Cove — Vienna, VA", "snippet": "dup", "confidence": 0.5, "provider": "web"},
    ]


def test_conversational_convergence_aggregate():
    state = assess_conversational_convergence()
    assert state["phase"] == "11.4.1"
    assert state["converged"] is True
    assert state["reliability"]["verified"] is True
    assert len(state["reliability"]["items"]) == 5
    assert "0.62" not in state["reliability"]["reply"]
    assert state["production_interaction"]["qualified"] is True
    assert state["qualification_tier"] == "production conversational"


def test_interaction_layers_separation():
    layers = describe_interaction_layers()
    assert len(layers["layers"]) == 6
    casual = layers["layers"]["casual_chat"]
    engineering = layers["layers"]["engineering_mode"]
    assert casual["telemetry_allowed"] is False
    assert engineering["telemetry_allowed"] is True
    assert resolve_surface(mode="casual") == "casual_chat"
    assert resolve_surface(mode="engineering") == "engineering_mode"


def test_surface_integrity_casual():
    clean = validate_surface_integrity(text="Here are five playgrounds.", mode="casual")
    assert clean["integrity_ok"] is True
    leak = validate_surface_integrity(text="confidence: medium / 0.62", mode="casual")
    assert leak["integrity_ok"] is False
    assert "telemetry_leak" in leak["violations"]


def test_trust_maturity_scoring():
    reliability = ensure_reliable_response(
        query="top five rated playgrounds in Virginia",
        evidence=_evidence(),
        overall_confidence=0.72,
    )
    harness = harness_state()
    trust = assess_trust_maturity(reliability=reliability, harness=harness)
    assert trust["trust_maturity_level"] in ("converging", "mature")
    assert trust["restraint_active"] is True


def test_production_interaction_qualification():
    reliability = ensure_reliable_response(
        query="top five rated playgrounds in Virginia",
        evidence=_evidence(),
        overall_confidence=0.72,
        include_followups=True,
    )
    harness = harness_state()
    trust = assess_trust_maturity(reliability=reliability, harness=harness)
    production = assess_production_interaction(reliability=reliability, harness=harness, trust=trust)
    assert production["qualified"] is True
    assert production["checks"]["intent_contracts_enforced"] is True


def test_maturity_profile_strategic_position():
    profile = build_maturity_profile(
        trust={"trust_maturity_level": "converging"},
        production={"qualified": True},
    )
    assert profile["strategic_position"] == "trustworthy operational product experience"
    assert profile["profile"]["production_realism"] == "next major frontier"


def test_capability_matrix_conversational_convergence():
    matrix = build_capability_truth_matrix()
    conv = next((r for r in matrix if r.get("id") == "conversational_convergence"), None)
    assert conv is not None and conv["verification_coverage_pct"] >= 90
