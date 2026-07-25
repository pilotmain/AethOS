# SPDX-License-Identifier: Apache-2.0
"""Phase 11.4.5 — Operational resilience cognition tests."""

from __future__ import annotations

from aethos_core.infrastructure_fragility.runtime import assess_infrastructure_fragility
from aethos_core.kubernetes_resilience.runtime import assess_kubernetes_resilience
from aethos_core.long_tail_resilience_memory.runtime import assess_long_tail_resilience_memory
from aethos_core.operational_resilience_cognition.resilience_runtime import orchestrate_operational_resilience
from aethos_core.operational_resilience_cognition.runtime import assess_operational_resilience_cognition
from aethos_core.operational_truth.capability_truth_matrix import build_capability_truth_matrix
from aethos_core.reality_harness_v43.harness_runtime import harness_state
from aethos_core.replay_resilience_intelligence.runtime import assess_replay_resilience_intelligence
from aethos_core.temporal_trust_evolution.runtime import assess_temporal_trust_evolution


def test_operational_resilience_cognition_aggregate():
    state = assess_operational_resilience_cognition()
    assert state["phase"] == "11.4.5"
    assert state["ok"] is True
    assert "remain resilient" in state["summary"].lower()
    assert "extended reconciliation" in state["narrative"].lower()
    assert state["harness"]["harness_version"] == "4.3"


def test_orchestrate_operational_resilience_narrative():
    resilience = orchestrate_operational_resilience()
    assert "remain resilient" in resilience["summary"].lower()
    assert "resilience regression" in resilience["summary"].lower()


def test_infrastructure_fragility():
    fragility = assess_infrastructure_fragility()
    assert fragility["ok"] is True
    assert fragility["fragility_elevated"] is False


def test_temporal_trust_evolution():
    trust = assess_temporal_trust_evolution()
    assert trust["ok"] is True
    assert "strengthening" in trust["summary"].lower()


def test_kubernetes_resilience():
    k8s = assess_kubernetes_resilience()
    assert k8s["ok"] is True
    assert k8s["resilient"] is True


def test_replay_resilience_intelligence():
    replay = assess_replay_resilience_intelligence()
    assert replay["ok"] is True
    assert "resilient" in replay["summary"].lower()


def test_long_tail_resilience_memory():
    memory = assess_long_tail_resilience_memory()
    assert memory["ok"] is True
    assert memory["memory_active"] is True


def test_reality_harness_v43():
    harness = harness_state()
    assert harness["harness_version"] == "4.3"
    assert harness["scenario_count"] == 8
    ids = {s["id"] for s in harness["scenarios"]}
    assert "prolonged_replay_pressure" in ids


def test_capability_matrix_operational_resilience_cognition():
    matrix = build_capability_truth_matrix()
    orc = next((r for r in matrix if r.get("id") == "operational_resilience_cognition"), None)
    assert orc is not None and orc["verification_coverage_pct"] >= 85
