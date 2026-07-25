# SPDX-License-Identifier: Apache-2.0
"""Phase 11.6.5 — Long-tail runtime cognition tests."""

from __future__ import annotations

from aethos_core.long_tail_runtime_cognition.cognition_runtime import orchestrate_long_tail_runtime_cognition
from aethos_core.long_tail_runtime_cognition.runtime import assess_long_tail_runtime_cognition
from aethos_core.operational_endurance.endurance_runtime import orchestrate_operational_endurance
from aethos_core.operational_truth.capability_truth_matrix import build_capability_truth_matrix
from aethos_core.reality_harness_v45.harness_runtime import harness_state
from aethos_core.replay_continuity_survivability.replay_survivability_runtime import orchestrate_replay_continuity_survivability
from aethos_core.resilience_exhaustion_intelligence.exhaustion_runtime import orchestrate_resilience_exhaustion_intelligence
from aethos_core.runtime_survivability_intelligence.survivability_runtime import orchestrate_runtime_survivability
from aethos_core.topology_endurance_forecasting.topology_runtime import orchestrate_topology_endurance


def test_long_tail_runtime_cognition_aggregate():
    state = assess_long_tail_runtime_cognition()
    assert state["phase"] == "11.6.5"
    assert state["ok"] is True
    assert "remain sustainable" in state["summary"].lower()
    assert "survivability degradation" in state["narrative"].lower()
    assert state["harness"]["harness_version"] == "4.5"


def test_orchestrate_long_tail_runtime_cognition_narrative():
    cognition = orchestrate_long_tail_runtime_cognition()
    assert "remain sustainable" in cognition["summary"].lower()
    assert "evolving operational conditions" in cognition["summary"].lower()


def test_runtime_survivability_intelligence():
    survivability = orchestrate_runtime_survivability()
    assert survivability["survivable"] is True
    assert "survivability" in survivability["summary"].lower()


def test_operational_endurance():
    endurance = orchestrate_operational_endurance()
    assert endurance["enduring"] is True
    assert "endurance" in endurance["summary"].lower()


def test_replay_continuity_survivability():
    replay = orchestrate_replay_continuity_survivability()
    assert replay["continuity_sustainable"] is True
    assert "sustained verification windows" in replay["summary"].lower()


def test_topology_endurance_forecasting():
    topology = orchestrate_topology_endurance()
    assert topology["enduring"] is True
    assert "long operational horizons" in topology["summary"].lower()


def test_resilience_exhaustion_intelligence():
    exhaustion = orchestrate_resilience_exhaustion_intelligence()
    assert exhaustion["exhaustion_emerging"] is False
    assert "resilience exhaustion" in exhaustion["summary"].lower()


def test_reality_harness_v45_runtime():
    harness = harness_state()
    assert harness["harness_version"] == "4.5"
    assert harness["scenario_count"] == 8
    ids = {s["id"] for s in harness["scenarios"]}
    assert "long_tail_survivability_erosion" in ids


def test_capability_matrix_long_tail_runtime_cognition():
    matrix = build_capability_truth_matrix()
    ltr = next((r for r in matrix if r.get("id") == "long_tail_runtime_cognition"), None)
    assert ltr is not None and ltr["verification_coverage_pct"] >= 89
