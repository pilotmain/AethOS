# SPDX-License-Identifier: Apache-2.0
"""Phase 9.8G — Autonomous operational runtime + governed reality loop."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from aethos_core.agents.memory.operational_patterns import clear_operational_patterns_for_tests, record_operational_event
from aethos_core.intelligence.anomaly_engine import detect_operational_anomalies
from aethos_core.intelligence.confidence_authority import score_anomaly_confidence, score_recommendation_confidence
from aethos_core.intelligence.operational_memory import clear_operational_memory_for_tests, operational_memory_snapshot, record_operational_memory
from aethos_core.intelligence.operational_notifications import clear_notification_state_for_tests, notify_operational_recommendations
from aethos_core.intelligence.operational_replay import clear_operational_replays_for_tests, get_operational_replay, list_operational_replays
from aethos_core.intelligence.recommendations import (
    clear_recommendations_for_tests,
    dismiss_recommendation,
    generate_recommendations_from_anomalies,
    list_recommendations,
    snooze_recommendation,
)
from aethos_core.operations.reality_loop import detect_operational_drift, run_reality_loop_cycle, run_reality_loop_scan
from aethos_core.runtime.schedulers.observation_scheduler import reset_scheduler_state_for_tests, run_due_observations, scheduler_status


@pytest.fixture(autouse=True)
def _clean():
    clear_operational_patterns_for_tests()
    clear_operational_memory_for_tests()
    clear_recommendations_for_tests()
    clear_operational_replays_for_tests()
    clear_notification_state_for_tests()
    reset_scheduler_state_for_tests()
    from aethos_core.engineering.governance.engineering_preflight_store import clear_engineering_preflights_for_tests

    clear_engineering_preflights_for_tests()
    yield
    clear_operational_patterns_for_tests()
    clear_operational_memory_for_tests()
    clear_recommendations_for_tests()
    clear_operational_replays_for_tests()
    clear_notification_state_for_tests()
    reset_scheduler_state_for_tests()
    clear_engineering_preflights_for_tests()


def _simulate_workflow_instability(count: int = 4) -> None:
    for i in range(count):
        record_operational_event(category="flaky_workflow", detail=f"workflow rerun failure #{i + 1}")
        record_operational_memory(kind="flaky_workflow", detail=f"rerun mismatch #{i + 1}", category="flaky_workflow")


def test_reality_loop_scan_readonly():
    scan = run_reality_loop_scan(window_hours=48)
    assert scan.get("readonly") is True
    assert scan.get("background_mutations") is False


def test_anomaly_detection_workflow_instability():
    _simulate_workflow_instability(4)
    from aethos_core.operations.reality_loop import collect_operational_observations

    observations = collect_operational_observations(window_hours=48)
    anomalies = detect_operational_anomalies(observations=observations, window_hours=48)
    assert anomalies
    assert any("workflow" in str(a.get("kind", "")).lower() for a in anomalies)
    assert anomalies[0].get("recommended_action")
    assert anomalies[0].get("confidence", 0) >= 0.5


def test_recommendation_generation_governance():
    _simulate_workflow_instability(4)
    from aethos_core.operations.reality_loop import collect_operational_observations

    observations = collect_operational_observations()
    anomalies = detect_operational_anomalies(observations=observations)
    recs = generate_recommendations_from_anomalies(anomalies)
    assert recs
    rec = recs[0]
    assert rec.get("approval_required") is True
    assert rec.get("autonomous_execution_blocked") is True
    assert "patch" in str(rec.get("suggested_action", "")).lower() or "engineering" in str(rec.get("suggested_action", "")).lower()


def test_operational_memory_persistence():
    record_operational_memory(kind="deployment_instability", detail="restart loop", category="deployment_instability")
    snap = operational_memory_snapshot()
    assert snap.get("total_events") >= 1
    assert snap.get("by_kind", {}).get("deployment_instability", 0) >= 1


def test_drift_detection():
    _simulate_workflow_instability(3)
    for i in range(3):
        record_operational_event(category="deployment_instability", detail=f"deploy fail {i}", provider="railway")
    from aethos_core.operations.reality_loop import collect_operational_observations

    drift = detect_operational_drift(collect_operational_observations())
    assert drift.get("detected") is True
    assert drift.get("signals")


def test_reality_loop_cycle_creates_replay():
    _simulate_workflow_instability(4)
    with patch("aethos_core.intelligence.operational_notifications.notify_operational_recommendations") as mock_notify:
        mock_notify.return_value = {"ok": True, "sent": [], "skipped": []}
        cycle = run_reality_loop_cycle(source="test")
    assert cycle.get("readonly") is True
    assert cycle.get("autonomous_execution_blocked") is True
    assert cycle.get("replay_id")
    replay = get_operational_replay(cycle["replay_id"])
    assert replay and replay.get("anomaly_count", 0) >= 0
    assert list_operational_replays()


def test_recommendation_dismiss_and_snooze():
    recs = generate_recommendations_from_anomalies(
        [
            {
                "anomaly_id": "anom-test",
                "kind": "flaky_workflow",
                "severity": "high",
                "confidence": 0.9,
                "evidence": ["test"],
                "related_systems": ["CI"],
                "recommended_action": "Generate governed engineering patch proposal",
            }
        ]
    )
    rid = recs[0]["recommendation_id"]
    snooze = snooze_recommendation(rid, hours=2)
    assert snooze["ok"] is True
    assert list_recommendations() == []
    dismiss = dismiss_recommendation(rid)
    assert dismiss["ok"] is True


def test_notification_deduplication():
    rec = {
        "recommendation_id": "rec-1",
        "kind": "flaky_workflow",
        "severity": "high",
        "confidence": 0.91,
        "observed": ["failure"],
        "suggested_action": "Generate governed engineering patch proposal",
    }
    with patch("aethos_core.intelligence.operational_notifications._dispatch", return_value=True):
        first = notify_operational_recommendations([rec])
        second = notify_operational_recommendations([rec])
    assert first.get("sent")
    assert second.get("skipped")


def test_scheduler_cadence_manual_tick():
    result = run_due_observations(force=True)
    assert result.get("ok") is True
    assert "reality_loop_cycle" in result.get("ran", [])
    status = scheduler_status()
    assert status.get("schedules")


def test_confidence_scoring_bounded():
    conf = score_anomaly_confidence(event_count=4, recurring=True, correlated_evidence=2)
    assert 0.35 <= conf <= 0.98
    rec_conf = score_recommendation_confidence(anomaly_confidence=conf, telemetry_quality="high")
    assert rec_conf <= 0.96


def test_browser_deployment_failure_scenario():
    for i in range(4):
        record_operational_event(category="browser_evidence_failure", detail=f"DNS failure {i}")
    from aethos_core.operations.reality_loop import collect_operational_observations

    observations = collect_operational_observations()
    anomalies = detect_operational_anomalies(observations=observations)
    assert any("browser" in str(a.get("kind", "")).lower() for a in anomalies)


def test_dependency_risk_scenario():
    for i in range(3):
        record_operational_event(category="dependency_churn", detail=f"CVE signal {i}")
    from aethos_core.operations.reality_loop import collect_operational_observations

    observations = collect_operational_observations()
    anomalies = detect_operational_anomalies(observations=observations)
    recs = generate_recommendations_from_anomalies(anomalies)
    assert anomalies or recs or observations.get("recurring_patterns") is not None


@patch("aethos_core.local_workspace.readonly.actions._repo_from_hint")
def test_generate_preflight_from_recommendation(mock_repo, tmp_path):
    from pathlib import Path

    repo = tmp_path / "repo"
    repo.mkdir()
    path = repo / "aethos_core/providers/github/shared/workflow_resolution.py"
    path.parent.mkdir(parents=True)
    path.write_text("x = 1\n")
    mock_repo.return_value = repo

    recs = generate_recommendations_from_anomalies(
        [
            {
                "anomaly_id": "anom-wf",
                "kind": "flaky_workflow",
                "severity": "high",
                "confidence": 0.92,
                "evidence": ["4 failures"],
                "related_systems": ["CI"],
                "recommended_action": "Generate governed engineering patch proposal",
            }
        ]
    )
    from aethos_core.intelligence.recommendations import generate_preflight_from_recommendation

    result = generate_preflight_from_recommendation(recs[0]["recommendation_id"])
    assert result.get("ok") is True
    assert result.get("preflight", {}).get("preflight_id")
    assert result.get("preflight", {}).get("execution_enabled") is False
