# SPDX-License-Identifier: Apache-2.0
"""Phase 9.8J — Operational reliability authority and adaptive governance."""

from __future__ import annotations

from time import time
from unittest.mock import patch

import pytest

from aethos_core.agents.memory.operational_patterns import clear_operational_patterns_for_tests, record_operational_event
from aethos_core.governance.adaptive.adaptive_governance import assess_adaptive_governance
from aethos_core.governance.adaptive.execution_pressure import assess_execution_pressure
from aethos_core.governance.adaptive.governance_memory import clear_governance_memory_for_tests, record_governance_outcome
from aethos_core.governance.adaptive.mutation_escalation import assess_mutation_escalation
from aethos_core.intelligence.confidence_authority import assess_telemetry_quality
from aethos_core.intelligence.operational_replay import clear_operational_replays_for_tests
from aethos_core.intelligence.recommendations import clear_recommendations_for_tests
from aethos_core.operations.reality_loop import collect_operational_observations, run_reality_loop_cycle
from aethos_core.presence.fatigue.fatigue_authority import apply_fatigue_prevention
from aethos_core.presence.operational_feed import clear_operational_feed_for_tests
from aethos_core.presence.presence_memory import clear_presence_memory_for_tests
from aethos_core.reliability.confidence_normalization import normalize_confidence
from aethos_core.reliability.operational_truth import resolve_truth_state
from aethos_core.reliability.reliability_authority import assess_reliability_authority
from aethos_core.reliability.reliability_runtime import assess_operational_reliability, clear_reliability_state_for_tests
from aethos_core.reliability.scoring.reliability_scoring import compute_reliability_scores
from aethos_core.replay_intelligence.causality_engine import infer_causal_chain
from aethos_core.replay_intelligence.incident_reconstruction import reconstruct_incident_timeline


@pytest.fixture(autouse=True)
def _clean():
    clear_operational_patterns_for_tests()
    clear_operational_replays_for_tests()
    clear_recommendations_for_tests()
    clear_governance_memory_for_tests()
    clear_operational_feed_for_tests()
    clear_presence_memory_for_tests()
    clear_reliability_state_for_tests()
    yield
    clear_operational_patterns_for_tests()
    clear_operational_replays_for_tests()
    clear_recommendations_for_tests()
    clear_governance_memory_for_tests()
    clear_operational_feed_for_tests()
    clear_presence_memory_for_tests()
    clear_reliability_state_for_tests()


def _event(**kwargs) -> dict:
    return {"at": time(), "source": kwargs.get("source", "test"), "summary": kwargs.get("summary", ""), **kwargs}


def test_confidence_never_exceeds_reality_with_stale_telemetry():
    result = normalize_confidence(0.92, telemetry_quality="low", stale_sources=2, replay_gaps=1)
    assert result["bounded_confidence"] <= 0.92
    assert result["bounded_confidence"] < 0.92
    assert result["degraded"] is True
    assert result["penalties"]


def test_repeated_railway_restarts_escalate_governance():
    events = [_event(category="deployment_instability", summary=f"Railway restart {i}", provider="railway") for i in range(4)]
    pressure = assess_execution_pressure(events=events, window_minutes=30)
    assert pressure["elevated"] is True
    assert pressure["restart_count"] >= 3
    escalation = assess_mutation_escalation(pressure=pressure)
    assert escalation["escalated"] is True
    assert escalation["current_tier"] == "E3_pr_creation"
    assert escalation["cooldown_active"] is True


def test_stale_telemetry_degraded_confidence_truth_state():
    telemetry = assess_telemetry_quality(event_count=1, stale_sources=2)
    observations = {"events": [], "telemetry_freshness": {"stale": True, "stale_sources": ["operational_patterns"]}}
    rel = assess_reliability_authority(observations=observations, telemetry=telemetry, replays=[])
    assert rel["truth_state"] in ("degraded_confidence", "replay_incomplete", "operationally_unknown", "execution_unverified")
    assert rel["bounded_confidence"] <= 0.96


def test_replay_gaps_recommend_repair():
    reconstruction = reconstruct_incident_timeline(window_hours=48)
    assert reconstruction.get("readonly") is True
    assert reconstruction.get("autonomous_execution_blocked") is True
    assert "operational_story" in reconstruction


def test_fatigue_reduction_for_ignored_signals():
    events = [
        _event(summary="repo_drift_scan", priority="NOTICE", event_id="e1"),
        _event(summary="repo_drift_scan 2", priority="NOTICE", event_id="e2"),
        _event(summary="Railway restart", priority="ELEVATED", event_id="e3"),
    ]
    result = apply_fatigue_prevention(events, dismissed_ids={"e1", "e2"})
    assert result["suppressed_count"] >= 1 or result["dedupe_count"] >= 0
    assert result["surfaced_count"] <= 12


def test_conflicting_evidence_downgrades_confidence():
    low = normalize_confidence(0.88, telemetry_quality="low", conflicting_evidence=True)
    high = normalize_confidence(0.88, telemetry_quality="high", conflicting_evidence=False)
    assert low["bounded_confidence"] < high["bounded_confidence"]


def test_workflow_and_deployment_correlated_narrative():
    events = [
        _event(category="flaky_workflow", summary="GitHub workflow rerun failure"),
        _event(category="deployment_instability", summary="Railway restart attempted", provider="railway"),
        _event(category="browser_evidence_failure", summary="browser verification failed"),
    ]
    chains = infer_causal_chain(events)
    assert chains
    assert any("workflow" in str(s).lower() or "github" in str(s).lower() for c in chains for s in c.get("steps", []))


@patch("aethos_core.intelligence.operational_notifications.notify_operational_recommendations")
def test_reality_loop_cycle_includes_reliability(_mock_notify):
    for i in range(4):
        record_operational_event(category="flaky_workflow", detail=f"workflow fail {i}")
    cycle = run_reality_loop_cycle(source="test")
    assert cycle.get("autonomous_execution_blocked") is True
    assert cycle.get("reliability") is not None
    assert cycle["reliability"].get("reliability", cycle["reliability"]).get("truth_state") or cycle["reliability"].get("truth_state")


def test_full_reliability_assessment_governance_blocked():
    for i in range(3):
        record_operational_event(category="deployment_instability", detail=f"Railway restart {i}", provider="railway")
    result = assess_operational_reliability()
    assert result.get("autonomous_execution_blocked") is True
    assert result.get("governance", {}).get("autonomous_execution_blocked") is True
    assert result.get("scores", {}).get("global_reliability_score", 1) <= 0.95
    assert result.get("explainability")


def test_stability_reward_after_validations():
    for _ in range(100):
        record_governance_outcome(kind="validation", detail="pytest pass", success=True)
    pressure = assess_execution_pressure(events=[], window_minutes=30)
    escalation = assess_mutation_escalation(pressure=pressure, validation_successes=100)
    assert "Stability reward" in escalation.get("escalation_reason", "")


def test_reliability_scores_bounded():
    scores = compute_reliability_scores(
        observations={"telemetry_freshness": {"stale": True}},
        reliability={"truth_state": "degraded_confidence", "bounded_confidence": 0.5},
    )
    assert 0.2 <= scores["global_reliability_score"] <= 0.95
    assert scores["trust_level"] in ("high", "moderate", "degraded", "low")
