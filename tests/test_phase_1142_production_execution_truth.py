# SPDX-License-Identifier: Apache-2.0
"""Phase 11.4.2 — Production execution realism tests."""

from __future__ import annotations

from aethos_core.infrastructure_truth.runtime import assess_infrastructure_truth
from aethos_core.operational_truth.capability_truth_matrix import build_capability_truth_matrix
from aethos_core.production_execution_truth.mutation_truth_convergence import converge_mutation_truth
from aethos_core.production_execution_truth.production_qualification import assess_production_qualification
from aethos_core.production_execution_truth.runtime import assess_production_execution_truth
from aethos_core.provider_truth_convergence.runtime import assess_provider_truth_convergence
from aethos_core.reality_harness_v4.harness_runtime import harness_state
from aethos_core.reality_harness_v4.scenarios import list_reality_scenarios_v4
from aethos_core.rollback_integrity.runtime import assess_rollback_integrity
from aethos_core.runtime_stabilization.runtime import assess_runtime_stabilization


def test_production_execution_truth_aggregate():
    state = assess_production_execution_truth()
    assert state["phase"] == "11.6"
    assert state["ok"] is True
    assert "extended monitoring" in state["narrative"].lower() or "monitoring" in state["summary"].lower()
    assert state["harness"]["harness_version"] == "4.0"
    assert state["production_qualification"]["qualification_tier"] in (
        "alpha", "beta", "stable", "production-reliable", "operationally-trusted",
    )


def test_mutation_truth_convergence_narrative():
    convergence = converge_mutation_truth(provider="railway")
    assert "stabilization" in convergence["summary"].lower()
    assert "monitoring" in convergence["narrative"].lower()


def test_provider_truth_convergence():
    providers = assess_provider_truth_convergence()
    assert providers["ok"] is True
    assert "railway" in providers["providers"]
    assert "github" in providers["providers"]
    assert "vercel" in providers["providers"]


def test_rollback_integrity():
    rollback = assess_rollback_integrity()
    assert rollback["ok"] is True
    assert "rollback" in rollback["summary"].lower()


def test_runtime_stabilization():
    stabilization = assess_runtime_stabilization()
    assert stabilization["ok"] is True
    assert stabilization["patience"]["premature_healthy_blocked"] is True


def test_infrastructure_truth():
    infra = assess_infrastructure_truth()
    assert infra["ok"] is True
    assert infra["score"]["infrastructure_truth_score"] >= 0.7


def test_reality_harness_v4():
    scenarios = list_reality_scenarios_v4()
    assert len(scenarios) == 8
    assert all(s["harness_version"] == "4.0" for s in scenarios)
    harness = harness_state()
    assert harness["verified_count"] >= 4


def test_production_qualification_tiers():
    harness = harness_state()
    qual = assess_production_qualification(
        deployment={"reality_qualified": True},
        rollback={"confidence": {"rollback_verified": True}},
        stabilization={"patience": {"premature_healthy_blocked": True}},
        infrastructure={"topology": {"converged": True}},
        harness=harness,
        decay={"decay_bounded": True},
    )
    assert qual["passed_count"] >= 5
    assert qual["qualification_tier"] in ("stable", "production-reliable", "operationally-trusted")


def test_capability_matrix_production_execution_truth():
    matrix = build_capability_truth_matrix()
    pet = next((r for r in matrix if r.get("id") == "production_execution_truth"), None)
    assert pet is not None and pet["verification_coverage_pct"] >= 80
