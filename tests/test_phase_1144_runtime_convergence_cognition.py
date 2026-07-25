# SPDX-License-Identifier: Apache-2.0
"""Phase 11.4.4 — Runtime convergence cognition tests."""

from __future__ import annotations

from aethos_core.infrastructure_intuition.runtime import assess_infrastructure_intuition
from aethos_core.kubernetes_convergence.runtime import assess_kubernetes_convergence
from aethos_core.long_tail_operational_memory.runtime import assess_long_tail_operational_memory
from aethos_core.operational_truth.capability_truth_matrix import build_capability_truth_matrix
from aethos_core.reality_harness_v42.harness_runtime import harness_state
from aethos_core.replay_continuity_intelligence.runtime import assess_replay_continuity_intelligence
from aethos_core.runtime_convergence_cognition.convergence_runtime import orchestrate_convergence_cognition
from aethos_core.runtime_convergence_cognition.runtime import assess_runtime_convergence_cognition
from aethos_core.temporal_confidence.runtime import assess_temporal_confidence


def test_runtime_convergence_cognition_aggregate():
    state = assess_runtime_convergence_cognition()
    assert state["phase"] == "11.4.4"
    assert state["ok"] is True
    assert "converge positively" in state["summary"].lower()
    assert "extended reconciliation" in state["narrative"].lower()
    assert state["harness"]["harness_version"] == "4.2"


def test_orchestrate_convergence_cognition_narrative():
    cognition = orchestrate_convergence_cognition()
    assert "operational stability continues to converge" in cognition["summary"].lower()
    assert "extended reconciliation" in cognition["summary"].lower()


def test_infrastructure_intuition():
    intuition = assess_infrastructure_intuition()
    assert intuition["ok"] is True
    assert intuition["intuition_active"] is True


def test_temporal_confidence():
    temporal = assess_temporal_confidence()
    assert temporal["ok"] is True
    assert "sustained verification" in temporal["summary"].lower()


def test_kubernetes_convergence():
    k8s = assess_kubernetes_convergence()
    assert k8s["ok"] is True
    assert k8s["converged"] is True


def test_replay_continuity_intelligence():
    replay = assess_replay_continuity_intelligence()
    assert replay["ok"] is True
    assert "sustained runtime windows" in replay["summary"].lower()


def test_long_tail_operational_memory():
    memory = assess_long_tail_operational_memory()
    assert memory["ok"] is True
    assert memory["memory_active"] is True


def test_reality_harness_v42():
    harness = harness_state()
    assert harness["harness_version"] == "4.2"
    assert harness["scenario_count"] == 8


def test_capability_matrix_runtime_convergence_cognition():
    matrix = build_capability_truth_matrix()
    ccg = next((r for r in matrix if r.get("id") == "runtime_convergence_cognition"), None)
    assert ccg is not None and ccg["verification_coverage_pct"] >= 85
