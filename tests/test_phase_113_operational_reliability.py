# SPDX-License-Identifier: Apache-2.0
"""Phase 11.3 — Autonomous operational verification tests."""

from __future__ import annotations

from aethos_core.continuous_verification.runtime import assess_continuous_verification
from aethos_core.drift_intelligence.runtime import assess_drift_intelligence
from aethos_core.operational_reliability.runtime import assess_operational_reliability
from aethos_core.operational_truth.capability_truth_matrix import build_capability_truth_matrix
from aethos_core.predictive_operations.runtime import assess_predictive_operations
from aethos_core.production_confidence.runtime import assess_production_confidence
from aethos_core.recovery_orchestration.runtime import orchestrate_recovery
from aethos_core.reliability_harness.scenarios import list_reliability_scenarios


def test_continuous_verification_summary():
    result = assess_continuous_verification()
    assert result["ok"] is True
    assert result["phase"] == "11.3"
    assert "extended observation" in result["summary"].lower() or "operational confidence" in result["summary"].lower()
    assert "Deployment verified successfully" not in result["summary"]


def test_recovery_orchestration_principle():
    result = orchestrate_recovery()
    assert result["ok"] is True
    assert "restart action" in result["principle"].lower()
    assert "dependencies" in result["principle"].lower()


def test_drift_intelligence_narrative():
    result = assess_drift_intelligence()
    assert result["ok"] is True
    assert "System healthy" not in result["summary"]
    assert "stable" in result["summary"].lower() or "monitor" in result["summary"].lower()


def test_predictive_operations():
    result = assess_predictive_operations()
    assert result["ok"] is True
    assert "instability" in result["principle"].lower()
    assert result.get("trajectory", {}).get("trajectory") in ("stable", "watch", "degrading")


def test_production_confidence_narrative():
    result = assess_production_confidence()
    assert result["ok"] is True
    assert "Confidence: high" not in result["narrative"]
    assert "confidence" in result["narrative"].lower()


def test_reliability_harness_v3():
    scenarios = list_reliability_scenarios()
    assert len(scenarios) == 8
    assert all(s["harness_version"] == "3.0" for s in scenarios)
    assert any(s["id"] == "prolonged_degradation" for s in scenarios)


def test_operational_reliability_aggregate():
    state = assess_operational_reliability()
    assert state["phase"] == "11.3"
    assert state["harness_version"] == "3.0"
    assert "continuous_verification" in state
    assert "production_confidence" in state


def test_capability_matrix_reliability_baselines():
    matrix = build_capability_truth_matrix()
    cv = next((r for r in matrix if r.get("id") == "continuous_verification"), None)
    pc = next((r for r in matrix if r.get("id") == "production_confidence"), None)
    assert cv is not None and cv["verification_coverage_pct"] >= 84
    assert pc is not None and pc["verification_coverage_pct"] >= 80
