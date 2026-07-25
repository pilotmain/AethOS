# SPDX-License-Identifier: Apache-2.0
"""Phase 11.4.7 — Long-tail operational forecasting tests."""

from __future__ import annotations

from aethos_core.autonomous_stability_cognition.cognition_runtime import orchestrate_autonomous_stability
from aethos_core.long_tail_operational_forecasting.forecasting_runtime import orchestrate_long_tail_forecasting
from aethos_core.long_tail_operational_forecasting.runtime import assess_long_tail_operational_forecasting
from aethos_core.operational_survivability.survivability_runtime import orchestrate_operational_survivability
from aethos_core.operational_truth.capability_truth_matrix import build_capability_truth_matrix
from aethos_core.reality_harness_v45.harness_runtime import harness_state
from aethos_core.replay_longevity_forecasting.replay_longevity_runtime import orchestrate_replay_longevity
from aethos_core.resilience_exhaustion.exhaustion_runtime import orchestrate_resilience_exhaustion
from aethos_core.topology_sustainability.topology_runtime import orchestrate_topology_sustainability


def test_long_tail_operational_forecasting_aggregate():
    state = assess_long_tail_operational_forecasting()
    assert state["phase"] == "11.4.7"
    assert state["ok"] is True
    assert "long-tail replay survivability" in state["summary"].lower()
    assert "survivability degradation" in state["narrative"].lower()
    assert state["harness"]["harness_version"] == "4.5"


def test_orchestrate_long_tail_forecasting_narrative():
    forecasting = orchestrate_long_tail_forecasting()
    assert "long-tail replay survivability" in forecasting["summary"].lower()
    assert "extended operational horizons" in forecasting["summary"].lower()


def test_operational_survivability():
    survivability = orchestrate_operational_survivability()
    assert survivability["survivable"] is True
    assert "survivability" in survivability["summary"].lower()


def test_replay_longevity_forecasting():
    replay = orchestrate_replay_longevity()
    assert replay["continuity_durable"] is True
    assert "sustained verification windows" in replay["summary"].lower()


def test_topology_sustainability():
    topology = orchestrate_topology_sustainability()
    assert topology["sustainable"] is True
    assert "extended operational horizons" in topology["summary"].lower()


def test_resilience_exhaustion():
    exhaustion = orchestrate_resilience_exhaustion()
    assert exhaustion["exhaustion_emerging"] is False
    assert "resilience exhaustion" in exhaustion["summary"].lower()


def test_autonomous_stability_cognition():
    stability = orchestrate_autonomous_stability()
    assert stability["stability_enduring"] is True
    assert "without panic escalation" in stability["summary"].lower()


def test_reality_harness_v45():
    harness = harness_state()
    assert harness["harness_version"] == "4.5"
    assert harness["scenario_count"] == 8
    ids = {s["id"] for s in harness["scenarios"]}
    assert "prolonged_replay_survivability_erosion" in ids


def test_capability_matrix_long_tail_operational_forecasting():
    matrix = build_capability_truth_matrix()
    ltf = next((r for r in matrix if r.get("id") == "long_tail_operational_forecasting"), None)
    assert ltf is not None and ltf["verification_coverage_pct"] >= 89
