# SPDX-License-Identifier: Apache-2.0
"""Phase 11.6.4 — Runtime fragility intelligence tests."""

from __future__ import annotations

from aethos_core.degradation_acceleration.runtime import assess_degradation_acceleration
from aethos_core.operational_fatigue_cognition.runtime import assess_operational_fatigue_cognition
from aethos_core.operational_truth.capability_truth_matrix import build_capability_truth_matrix
from aethos_core.predictive_runtime_stability.runtime import assess_predictive_runtime_stability
from aethos_core.reality_harness_v44.harness_runtime import harness_state
from aethos_core.replay_erosion_intelligence.runtime import assess_replay_erosion_intelligence
from aethos_core.runtime_fragility_intelligence.fragility_runtime import orchestrate_runtime_fragility
from aethos_core.runtime_fragility_intelligence.runtime import assess_runtime_fragility_intelligence
from aethos_core.topology_fragility_forecasting.runtime import assess_topology_fragility_forecasting


def test_runtime_fragility_intelligence_aggregate():
    state = assess_runtime_fragility_intelligence()
    assert state["phase"] == "11.6.4"
    assert state["ok"] is True
    assert "remain resilient" in state["summary"].lower()
    assert "fragility monitoring" in state["narrative"].lower()
    assert state["harness"]["harness_version"] == "4.4"


def test_orchestrate_runtime_fragility_narrative():
    fragility = orchestrate_runtime_fragility()
    assert "remain resilient" in fragility["summary"].lower()
    assert "instability acceleration" in fragility["summary"].lower()


def test_degradation_acceleration():
    acceleration = assess_degradation_acceleration()
    assert acceleration["ok"] is True
    assert acceleration["acceleration_detected"] is False


def test_replay_erosion_intelligence():
    replay = assess_replay_erosion_intelligence()
    assert replay["ok"] is True
    assert "moderate replay erosion pressure" in replay["summary"].lower()


def test_topology_fragility_forecasting():
    topology = assess_topology_fragility_forecasting()
    assert topology["ok"] is True
    assert topology["fragility_bounded"] is True


def test_operational_fatigue_cognition():
    fatigue = assess_operational_fatigue_cognition()
    assert fatigue["ok"] is True
    assert "prolonged stabilization pressure" in fatigue["summary"].lower()


def test_predictive_runtime_stability():
    stability = assess_predictive_runtime_stability()
    assert stability["ok"] is True
    assert stability["stability_projected"] is True


def test_reality_harness_v44_fragility():
    harness = harness_state()
    assert harness["harness_version"] == "4.4"
    assert harness["scenario_count"] == 8


def test_capability_matrix_runtime_fragility_intelligence():
    matrix = build_capability_truth_matrix()
    rfi = next((r for r in matrix if r.get("id") == "runtime_fragility_intelligence"), None)
    assert rfi is not None and rfi["verification_coverage_pct"] >= 88
