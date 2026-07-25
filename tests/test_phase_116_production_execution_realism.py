# SPDX-License-Identifier: Apache-2.0
"""Phase 11.6 — Production execution realism tests."""

from __future__ import annotations

from aethos_core.operational_truth.capability_truth_matrix import build_capability_truth_matrix
from aethos_core.production_execution.runtime import assess_production_execution_realism
from aethos_core.production_execution_truth.execution_patience import assess_execution_patience
from aethos_core.production_execution_truth.mutation_truth_convergence import converge_mutation_truth
from aethos_core.production_execution_truth.runtime import assess_production_execution_truth
from aethos_core.provider_truth_convergence.railway_runtime_truth import assess_railway_runtime_truth
from aethos_core.reality_harness_v4.scenarios import list_reality_scenarios_v4
from aethos_core.runtime_stabilization.recovery_patience import assess_recovery_patience
from aethos_core.sustained_verification.runtime import assess_sustained_verification


def test_production_execution_realism_aggregate():
    state = assess_production_execution_realism()
    assert state["phase"] == "11.6"
    assert state["ok"] is True
    assert "dependency health" in state["summary"].lower() or "infrastructure" in state["summary"].lower()
    assert state["sustained_verification"]["ok"] is True
    assert state["harness"]["harness_version"] == "4.0"


def test_production_execution_truth_phase():
    state = assess_production_execution_truth()
    assert state["phase"] == "11.6"
    assert "execution_patience" in state["execution_truth"]


def test_mutation_truth_convergence_116_narrative():
    convergence = converge_mutation_truth(provider="railway")
    assert "telemetry freshness" in convergence["summary"].lower()
    assert "monitoring" in convergence["narrative"].lower()


def test_execution_patience_blocks_premature_claims():
    patience = assess_execution_patience(
        stabilization={"stabilization_complete": False, "extended_monitoring_active": True},
        verification={"verified": False},
    )
    assert patience["premature_claim_blocked"] is True


def test_railway_runtime_truth():
    truth = assess_railway_runtime_truth()
    assert truth["provider"] == "railway"
    assert "stabilization" in truth["summary"].lower()


def test_sustained_verification():
    sustained = assess_sustained_verification()
    assert sustained["ok"] is True
    assert sustained["drift_reverification"]["drift_bounded"] is True
    assert sustained["extended_monitoring_active"] is True


def test_recovery_patience():
    patience = assess_recovery_patience(
        stabilization={"stabilization_complete": False},
        verification={"verified": False},
    )
    assert patience["recovery_patience_active"] is True


def test_reality_harness_v4_scenarios_116():
    scenarios = list_reality_scenarios_v4()
    assert len(scenarios) == 8
    ids = {s["id"] for s in scenarios}
    assert "kubernetes_rollout_erosion" in ids
    assert "telemetry_drift" in ids


def test_capability_matrix_production_execution_realism():
    matrix = build_capability_truth_matrix()
    realism = next((r for r in matrix if r.get("id") == "production_execution_realism"), None)
    sustained = next((r for r in matrix if r.get("id") == "sustained_verification"), None)
    assert realism is not None and realism["verification_coverage_pct"] >= 80
    assert sustained is not None and sustained["verification_coverage_pct"] >= 80
