# SPDX-License-Identifier: Apache-2.0
"""Phase 11.4.6 — Predictive operational cognition tests."""

from __future__ import annotations

from aethos_core.fragility_acceleration.runtime import assess_fragility_acceleration
from aethos_core.operational_fatigue_intelligence.runtime import assess_operational_fatigue_intelligence
from aethos_core.operational_truth.capability_truth_matrix import build_capability_truth_matrix
from aethos_core.predictive_operational_cognition.predictive_runtime import orchestrate_predictive_cognition
from aethos_core.predictive_operational_cognition.runtime import assess_predictive_operational_cognition
from aethos_core.reality_harness_v44.harness_runtime import harness_state
from aethos_core.replay_erosion_forecasting.runtime import assess_replay_erosion_forecasting
from aethos_core.sustained_stability_forecasting.runtime import assess_sustained_stability_forecasting
from aethos_core.topology_stability_forecasting.runtime import assess_topology_stability_forecasting


def test_predictive_operational_cognition_aggregate():
    state = assess_predictive_operational_cognition()
    assert state["phase"] == "11.4.6"
    assert state["ok"] is True
    assert "future instability risk" in state["summary"].lower()
    assert "predictive monitoring" in state["narrative"].lower()
    assert state["harness"]["harness_version"] == "4.4"


def test_orchestrate_predictive_cognition_narrative():
    cognition = orchestrate_predictive_cognition()
    assert "future instability risk" in cognition["summary"].lower()
    assert "predictive degradation" in cognition["summary"].lower()


def test_fragility_acceleration():
    acceleration = assess_fragility_acceleration()
    assert acceleration["ok"] is True
    assert acceleration["acceleration_detected"] is False


def test_replay_erosion_forecasting():
    replay = assess_replay_erosion_forecasting()
    assert replay["ok"] is True
    assert "moderate replay erosion pressure" in replay["summary"].lower()


def test_topology_stability_forecasting():
    topology = assess_topology_stability_forecasting()
    assert topology["ok"] is True
    assert topology["topology_stable"] is True


def test_operational_fatigue_intelligence():
    fatigue = assess_operational_fatigue_intelligence()
    assert fatigue["ok"] is True
    assert "prolonged runtime stabilization pressure" in fatigue["summary"].lower()


def test_sustained_stability_forecasting():
    forecast = assess_sustained_stability_forecasting()
    assert forecast["ok"] is True
    assert forecast["stability_projected"] is True


def test_reality_harness_v44():
    harness = harness_state()
    assert harness["harness_version"] == "4.4"
    assert harness["scenario_count"] == 8
    ids = {s["id"] for s in harness["scenarios"]}
    assert "prolonged_replay_erosion" in ids


def test_capability_matrix_predictive_operational_cognition():
    matrix = build_capability_truth_matrix()
    poc = next((r for r in matrix if r.get("id") == "predictive_operational_cognition"), None)
    assert poc is not None and poc["verification_coverage_pct"] >= 85
