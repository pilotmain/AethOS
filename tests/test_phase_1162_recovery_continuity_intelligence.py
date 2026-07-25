# SPDX-License-Identifier: Apache-2.0
"""Phase 11.6.2 — Recovery continuity intelligence tests."""

from __future__ import annotations

from aethos_core.adaptive_runtime_verification.runtime import assess_adaptive_runtime_verification
from aethos_core.infrastructure_convergence.runtime import assess_infrastructure_convergence
from aethos_core.long_tail_stability.runtime import assess_long_tail_stability
from aethos_core.operational_truth.capability_truth_matrix import build_capability_truth_matrix
from aethos_core.reality_harness_v42.harness_runtime import harness_state
from aethos_core.recovery_continuity.continuity_runtime import orchestrate_recovery_continuity
from aethos_core.recovery_continuity.runtime import assess_recovery_continuity_intelligence
from aethos_core.replay_persistence.runtime import assess_replay_persistence_intelligence
from aethos_core.temporal_operational_trust.runtime import assess_temporal_operational_trust


def test_recovery_continuity_intelligence_aggregate():
    state = assess_recovery_continuity_intelligence()
    assert state["phase"] == "11.6.2"
    assert state["ok"] is True
    assert "remain stable" in state["summary"].lower()
    assert "adaptive verification" in state["narrative"].lower()
    assert state["harness"]["harness_version"] == "4.2"


def test_orchestrate_recovery_continuity_narrative():
    continuity = orchestrate_recovery_continuity()
    assert "operational recovery continues" in continuity["summary"].lower()
    assert "adaptive verification remains active" in continuity["summary"].lower()


def test_temporal_operational_trust():
    trust = assess_temporal_operational_trust()
    assert trust["ok"] is True
    assert "strengthening" in trust["summary"].lower()


def test_infrastructure_convergence():
    infra = assess_infrastructure_convergence()
    assert infra["ok"] is True
    assert infra["converging"] is True


def test_replay_persistence_intelligence():
    replay = assess_replay_persistence_intelligence()
    assert replay["ok"] is True
    assert "sustained operational verification" in replay["summary"].lower()


def test_adaptive_runtime_verification():
    adaptive = assess_adaptive_runtime_verification()
    assert adaptive["ok"] is True
    assert "adaptive" in adaptive["summary"].lower()


def test_long_tail_stability():
    stability = assess_long_tail_stability()
    assert stability["ok"] is True
    assert stability["long_tail_stable"] is True


def test_reality_harness_v42_recovery_scenarios():
    harness = harness_state()
    assert harness["harness_version"] == "4.2"
    assert harness["scenario_count"] == 8
    ids = {s["id"] for s in harness["scenarios"]}
    assert "delayed_replay_erosion" in ids


def test_capability_matrix_recovery_continuity_intelligence():
    matrix = build_capability_truth_matrix()
    rci = next((r for r in matrix if r.get("id") == "recovery_continuity_intelligence"), None)
    assert rci is not None and rci["verification_coverage_pct"] >= 85
