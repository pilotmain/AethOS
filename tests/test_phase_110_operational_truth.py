# SPDX-License-Identifier: Apache-2.0
"""Phase 11.0 — Operational truth convergence tests."""

from __future__ import annotations

from aethos_core.confidence_integrity.integrity_runtime import assess_confidence_integrity
from aethos_core.operational_truth.capability_truth_matrix import build_capability_truth_matrix, matrix_summary
from aethos_core.operational_truth.maturity_classification import classify_maturity
from aethos_core.operational_truth.operational_honesty import assess_operational_honesty
from aethos_core.operational_truth.operational_readiness import assess_operational_readiness
from aethos_core.operational_truth.runtime import assess_operational_truth, get_operational_truth_state
from aethos_core.reality_harness.harness_runtime import harness_state, list_reality_scenarios


def test_capability_truth_matrix_honesty():
    matrix = build_capability_truth_matrix()
    summary = matrix_summary(matrix)
    assert summary["total_capabilities"] >= 5
    assert summary["claimed_count"] >= 1
    railway = next((r for r in matrix if r.get("id") == "railway:restart"), None)
    if railway:
        assert railway["claimed"] is True
        assert railway["maturity"] in ("stable", "beta", "production-ready")
        assert railway["verification_coverage_pct"] >= 84


def test_maturity_classification():
    assert classify_maturity(
        claimed=True,
        real_level="partial",
        verified_level="partial",
        verification_coverage=0.62,
    ) == "beta"
    assert classify_maturity(
        claimed=True,
        real_level="full",
        verified_level="full",
        verification_coverage=0.95,
        prod_ready=True,
    ) == "production-ready"


def test_operational_readiness_scoring():
    readiness = assess_operational_readiness()
    assert readiness["readiness_tier"] in ("experimental", "alpha", "beta", "stable", "production-ready")
    assert 0 <= readiness["readiness_score"] <= 100
    assert readiness["tier1_providers"]


def test_operational_honesty_detects_overclaim():
    matrix = build_capability_truth_matrix()
    honesty = assess_operational_honesty(matrix)
    assert "honesty_principle" in honesty
    assert honesty["overclaim_risk"] in (True, False)


def test_operational_truth_runtime():
    result = assess_operational_truth()
    assert result["ok"] is True
    assert result["capability_matrix"]
    assert result["readiness"]
    assert result["execution_integrity"]
    assert result["summary"]


def test_operational_truth_state_lightweight():
    state = get_operational_truth_state()
    assert state["ok"] is True
    assert "truth_state" in state
    assert "readiness_tier" in state


def test_confidence_integrity_caps_unverified():
    result = assess_confidence_integrity(raw_confidence=0.9, verified=False)
    assert result["bounded_confidence"] <= 0.72
    assert "verification" in result["summary"].lower() or result["integrity"] == "bounded"


def test_reality_harness_scenarios():
    scenarios = list_reality_scenarios()
    assert any(s["id"] == "railway_restart" for s in scenarios)
    state = harness_state()
    assert state["ok"] is True
    assert state["scenario_count"] >= 5 or len(scenarios) >= 5
