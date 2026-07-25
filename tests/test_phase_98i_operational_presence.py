# SPDX-License-Identifier: Apache-2.0
"""Phase 9.8I — Ambient operational presence."""

from __future__ import annotations

from time import time

import pytest

from aethos_core.agents.memory.operational_patterns import clear_operational_patterns_for_tests, record_operational_event
from aethos_core.chat.presence_intelligence import execute_presence_intelligence, is_presence_intelligence_request
from aethos_core.intelligence.recommendations import clear_recommendations_for_tests, generate_recommendations_from_anomalies
from aethos_core.presence.attention_engine import rank_feed_events, score_attention
from aethos_core.presence.collaboration_state import clear_collaboration_state_for_tests, start_collaboration_session
from aethos_core.presence.interruption_policy import clear_interruption_state_for_tests, should_notify
from aethos_core.presence.operational_feed import aggregate_operational_feed, clear_operational_feed_for_tests, list_feed_events
from aethos_core.presence.presence_memory import clear_presence_memory_for_tests, presence_memory_snapshot, record_presence_event
from aethos_core.presence.presence_runtime import dismiss_presence_recommendation, run_presence_cycle, synthesize_operational_brief
from aethos_core.presence.presence_sessions import clear_presence_sessions_for_tests
from aethos_core.presence.replay_bridge import build_presence_timeline
from aethos_core.presence.watch_mode import clear_watchers_for_tests, register_watcher, tick_watchers


@pytest.fixture(autouse=True)
def _clean():
    clear_operational_patterns_for_tests()
    clear_operational_feed_for_tests()
    clear_presence_memory_for_tests()
    clear_presence_sessions_for_tests()
    clear_collaboration_state_for_tests()
    clear_interruption_state_for_tests()
    clear_watchers_for_tests()
    clear_recommendations_for_tests()
    yield
    clear_operational_patterns_for_tests()
    clear_operational_feed_for_tests()
    clear_presence_memory_for_tests()
    clear_presence_sessions_for_tests()
    clear_collaboration_state_for_tests()
    clear_interruption_state_for_tests()
    clear_watchers_for_tests()
    clear_recommendations_for_tests()


def test_attention_scoring_high_severity():
    att = score_attention(severity="high", confidence=0.9, recurrence=3, operational_impact=True)
    assert att["priority"] in ("urgent", "critical", "elevated")
    assert att["attention_score"] >= 0.5


def test_feed_aggregation():
    record_operational_event(category="deployment_instability", detail="Railway restart", provider="railway")
    record_operational_event(category="flaky_workflow", detail="workflow rerun fail")
    record_operational_event(category="flaky_workflow", detail="workflow rerun fail 2")
    feed = aggregate_operational_feed(window_hours=48)
    assert feed
    assert list_feed_events()


def test_timeline_replay_generation():
    record_operational_event(category="dependency_churn", detail="CVE signal")
    aggregate_operational_feed(window_hours=48)
    timeline = build_presence_timeline(window_hours=48)
    assert timeline.get("artifact_type") == "presence_operational_timeline"
    assert timeline.get("timeline_id")


def test_recommendation_dedupe_via_intelligence():
    anomalies = [
        {
            "anomaly_id": "a1",
            "kind": "flaky_workflow",
            "severity": "high",
            "confidence": 0.9,
            "evidence": ["x"],
            "related_systems": ["CI"],
            "recommended_action": "Generate governed engineering patch proposal",
        }
    ]
    first = generate_recommendations_from_anomalies(anomalies)
    second = generate_recommendations_from_anomalies(anomalies)
    assert len(first) == 1
    assert len(second) == 0


def test_watch_mode_cooldown():
    register_watcher(target="github_workflow")
    record_operational_event(category="flaky_workflow", detail="f1")
    record_operational_event(category="flaky_workflow", detail="f2")
    record_operational_event(category="flaky_workflow", detail="f3")
    first = tick_watchers()
    second = tick_watchers()
    assert first.get("autonomous_execution_blocked") is True
    assert len(second.get("alerts") or []) == 0


def test_notification_suppression_on_focus():
    start_collaboration_session(focus="engineering_debug")
    assert should_notify(fingerprint="test:passive", priority="passive", focus_mode="engineering_debug") is False
    assert should_notify(fingerprint="test:urgent", priority="urgent", focus_mode="engineering_debug") is True


def test_collaboration_session():
    sess = start_collaboration_session(focus="deployment_debug", investigation="Railway instability")
    assert sess.get("session_id")
    assert sess.get("focus") == "deployment_debug"


def test_presence_memory_persistence():
    record_presence_event(kind="deployment", detail="failed deploy")
    snap = presence_memory_snapshot()
    assert snap.get("deployments_count", 0) >= 1 or snap.get("incidents_count", 0) >= 1


def test_presence_cycle_governance():
    cycle = run_presence_cycle(session_id="test")
    assert cycle.get("autonomous_execution_blocked") is True
    assert cycle.get("readonly") is True


def test_operational_brief_synthesis():
    record_operational_event(category="flaky_workflow", detail="workflow failure")
    aggregate_operational_feed(window_hours=48)
    brief = synthesize_operational_brief(window_hours=2)
    assert "Operational brief" in brief
    assert "Governance" in brief


def test_presence_chat_lane():
    assert is_presence_intelligence_request("What should I pay attention to today?")
    result = execute_presence_intelligence("What changed in the last 2 hours?", session_id="test")
    assert result is not None
    body, intent, meta = result
    assert intent == "operational_presence"
    assert meta.get("autonomous_execution_blocked") == "true"


def test_dismiss_recommendation_records_memory():
    recs = generate_recommendations_from_anomalies(
        [
            {
                "anomaly_id": "a2",
                "kind": "deployment_instability",
                "severity": "high",
                "confidence": 0.88,
                "evidence": ["restart"],
                "related_systems": ["Railway"],
                "recommended_action": "Inspect deployment timeline",
            }
        ]
    )
    rid = recs[0]["recommendation_id"]
    result = dismiss_presence_recommendation(rid)
    assert result.get("ok") is True
    snap = presence_memory_snapshot()
    assert any(d.get("id") == rid for d in snap.get("dismissed") or [])


def test_rank_feed_events():
    events = [
        {"severity": "low", "confidence": 0.5, "summary": "info", "at": time()},
        {"severity": "high", "confidence": 0.9, "summary": "critical", "at": time(), "operational_impact": True},
    ]
    ranked = rank_feed_events(events)
    assert ranked[0]["summary"] == "critical"
