# SPDX-License-Identifier: Apache-2.0
"""Phase 9.8I.1 — Presence signal quality and operational relevance."""

from __future__ import annotations

from time import time

import pytest

from aethos_core.agents.memory.operational_patterns import clear_operational_patterns_for_tests, record_operational_event
from aethos_core.presence.attention_authority import rank_with_attention_authority, score_attention_quality
from aethos_core.presence.collaboration_state import clear_collaboration_state_for_tests, start_collaboration_session
from aethos_core.presence.operational_feed import clear_operational_feed_for_tests
from aethos_core.presence.presence_brief_synthesis import synthesize_operator_brief
from aethos_core.presence.presence_clustering import cluster_operational_signals, list_operational_incidents
from aethos_core.presence.presence_memory import clear_presence_memory_for_tests, record_presence_event
from aethos_core.presence.presence_memory_compaction import compact_presence_memory
from aethos_core.presence.presence_reasoning import infer_operational_intent, route_signals_by_context
from aethos_core.presence.presence_recommendation_intelligence import synthesize_intelligent_recommendations
from aethos_core.presence.presence_runtime import synthesize_operational_brief
from aethos_core.presence.presence_signal_pipeline import process_presence_signals
from aethos_core.presence.presence_sessions import clear_presence_sessions_for_tests
from aethos_core.presence.signal_deduplication import deduplicate_signals


@pytest.fixture(autouse=True)
def _clean():
    clear_operational_patterns_for_tests()
    clear_operational_feed_for_tests()
    clear_presence_memory_for_tests()
    clear_presence_sessions_for_tests()
    clear_collaboration_state_for_tests()
    yield
    clear_operational_patterns_for_tests()
    clear_operational_feed_for_tests()
    clear_presence_memory_for_tests()
    clear_presence_sessions_for_tests()
    clear_collaboration_state_for_tests()


def _event(source: str, summary: str, **extra) -> dict:
    return {
        "event_id": f"evt-{summary[:8]}",
        "at": time(),
        "source": source,
        "summary": summary,
        "severity": extra.pop("severity", "medium"),
        "confidence": extra.pop("confidence", 0.75),
        **extra,
    }


def test_deduplication_collapses_repo_drift_scans():
    events = [
        _event("operational_drift", "repo_drift_scan workspace-a"),
        _event("operational_drift", "repo_drift_scan workspace-b"),
        _event("operational_drift", "repo_drift_scan workspace-c"),
        _event("operational_drift", "repo_drift_scan workspace-d"),
        _event("operational_drift", "repo_drift_scan workspace-e"),
    ]
    deduped = deduplicate_signals(events)
    assert len(deduped) == 1
    assert deduped[0].get("dedupe_count") == 5
    assert "Repeated repository drift" in deduped[0]["summary"]
    assert deduped[0].get("signal_class") == "internal_substrate"


def test_deployment_question_routes_away_from_repo_drift():
    events = [
        _event("operational_drift", "repo_drift_scan main", signal_class="internal_substrate"),
        _event("deployment_instability", "Railway restart attempt", provider="railway", operational_impact=True),
        _event("flaky_workflow", "GitHub workflow rerun failure", provider="github"),
    ]
    intent = infer_operational_intent("Any recurring deployment instability?")
    assert intent == "deployment"
    routed = route_signals_by_context(deduplicate_signals(events), intent=intent)
    summaries = " ".join(str(e.get("summary") or "") for e in routed).lower()
    assert "railway" in summaries or "workflow" in summaries
    assert "repo_drift" not in summaries


def test_attention_authority_repo_drift_not_urgent():
    att = score_attention_quality(
        _event("operational_drift", "repo_drift_scan", signal_class="internal_substrate", severity="high")
    )
    assert att["priority"] == "PASSIVE"
    assert att["attention_score"] < 0.4


def test_attention_authority_repeated_deployment_elevated():
    events = [
        _event("deployment_instability", "Railway restart loop", recurrence=3, operational_impact=True),
        _event("flaky_workflow", "GitHub rerun failed", recurrence=2, provider="github"),
    ]
    clusters = cluster_operational_signals(events)
    scored = rank_with_attention_authority(
        route_signals_by_context(events, intent="deployment"),
        clusters=clusters,
    )
    priorities = {str(e.get("priority")) for e in scored}
    assert "PASSIVE" not in priorities or len(priorities) > 1
    assert any(p in priorities for p in ("ELEVATED", "URGENT", "NOTICE"))


def test_clustering_groups_deployment_incidents():
    events = [
        _event("deployment_instability", "Railway restart", provider="railway"),
        _event("flaky_workflow", "GitHub workflow rerun failure"),
        _event("deployment_instability", "Vercel rollout anomaly", provider="vercel"),
    ]
    clusters = cluster_operational_signals(events)
    incidents = list_operational_incidents(clusters)
    themes = {c.get("theme") for c in incidents}
    assert "deployment_instability" in themes or "workflow_instability" in themes
    assert incidents[0].get("event_count", 0) >= 2


def test_intelligent_recommendations_for_workflow_and_deployment():
    events = [
        _event("deployment_instability", "Railway restart attempt", provider="railway"),
        _event("deployment_instability", "Railway health check failed", provider="railway"),
        _event("flaky_workflow", "GitHub workflow rerun failure"),
        _event("flaky_workflow", "GitHub workflow rerun failure 2"),
    ]
    clusters = cluster_operational_signals(events)
    scored = rank_with_attention_authority(route_signals_by_context(events, intent="deployment"), clusters=clusters)
    recs = synthesize_intelligent_recommendations(clusters=clusters, scored_events=scored)
    assert recs
    actions = " ".join(str(r.get("suggested_action") or "") for r in recs).lower()
    assert "workflow" in actions or "deployment" in actions or "preflight" in actions
    assert all(r.get("approval_required") for r in recs)


def test_focus_deployment_debug_prioritizes_deployment_signals():
    start_collaboration_session(focus="deployment_debug", investigation="Railway instability")
    events = [
        _event("dependency_churn", "npm package drift detected"),
        _event("operational_drift", "repo_drift_scan", signal_class="internal_substrate"),
        _event("deployment_instability", "Railway restart loop", provider="railway"),
        _event("flaky_workflow", "GitHub workflow rerun failure"),
    ]
    processed = process_presence_signals(events, focus={"mode": "deployment_debug"})
    assert processed.get("intent") == "deployment"
    top = (processed.get("events") or [])[:2]
    joined = " ".join(str(e.get("summary") or "") for e in top).lower()
    assert "railway" in joined or "workflow" in joined or "github" in joined


def test_operator_brief_quality():
    events = [
        _event("deployment_instability", "Railway restart attempt", provider="railway", priority="ELEVATED"),
        _event("flaky_workflow", "GitHub workflow rerun instability", priority="ELEVATED"),
    ]
    clusters = cluster_operational_signals(events)
    recs = synthesize_intelligent_recommendations(clusters=clusters, scored_events=events)
    brief = synthesize_operator_brief(
        window_hours=2,
        events=events,
        clusters=clusters,
        recommendations=recs,
        intent="deployment",
    )
    assert "Operational brief" in brief
    assert "Governance" in brief
    assert "repo_drift" not in brief.lower()
    assert "Railway" in brief or "deployment" in brief.lower() or "workflow" in brief.lower()


def test_end_to_end_brief_from_operational_patterns():
    record_operational_event(category="deployment_instability", detail="Railway restart", provider="railway")
    record_operational_event(category="flaky_workflow", detail="GitHub workflow rerun failure")
    record_operational_event(category="operational_drift", detail="repo_drift_scan scheduled")
    record_operational_event(category="operational_drift", detail="repo_drift_scan scheduled 2")
    brief = synthesize_operational_brief(
        window_hours=2,
        user_text="Any recurring deployment instability?",
    )
    assert "repo_drift_scan" not in brief
    assert "Governance" in brief


def test_memory_compaction_collapses_low_value_events():
    for _ in range(4):
        record_presence_event(kind="operational_drift", detail="repo_drift_scan scheduled")
    record_presence_event(kind="deployment", detail="Railway restart failure")
    result = compact_presence_memory()
    assert result.get("ok") is True
    patterns = result.get("compacted_patterns") or []
    assert not any("repo_drift_scan" in str(p) for p in patterns) or result.get("incidents_remaining", 0) <= 2


def test_attention_quality_summary_reduces_inflation():
    events = [
        {"priority": "PASSIVE", "summary": "repo drift"},
        {"priority": "PASSIVE", "summary": "repo drift 2"},
        {"priority": "ELEVATED", "summary": "deployment"},
    ]
    from aethos_core.presence.attention_authority import attention_quality_summary

    quality = attention_quality_summary(events)
    assert quality.get("passive_count", 0) >= 2
    assert quality.get("urgency_inflation_ratio", 1) <= 0.5
