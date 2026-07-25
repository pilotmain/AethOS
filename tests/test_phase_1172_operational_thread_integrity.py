# SPDX-License-Identifier: Apache-2.0
"""Phase 11.7.2 — Operational thread integrity tests."""

from __future__ import annotations

from aethos_core.continuity_reconstruction.continuity_decay import apply_decay_to_confidence, compute_continuity_decay
from aethos_core.continuity_reconstruction.thread_isolation import score_thread_isolation
from aethos_core.conversation.legacy_polish_api import assess_conversational_operational_grounding
from aethos_core.operational_context_memory.investigation_lifecycle import assess_investigation_lifecycle, snapshot_investigation
from aethos_core.operational_context_memory.memory_precedence import reconcile_memory_layers
from aethos_core.operational_thread_integrity.runtime import assess_operational_thread_integrity
from aethos_core.conversation.operational_memory import clear_operational_memory_for_tests, persist_investigation, record_focus_recovery
from aethos_core.operational_context_memory.context_store import persist_operational_context


def _seed(session_id: str = "test-1172") -> None:
    clear_operational_memory_for_tests()
    record_focus_recovery(session_id=session_id, focus="Railway deployment recovery", channel="telegram")
    persist_investigation(session_id=session_id, investigation="replay continuity durability")
    persist_operational_context(
        session_id=session_id,
        context={"deployment_subject": "Railway deployment recovery", "latest_investigation": "replay continuity durability"},
    )
    snapshot_investigation(session_id=session_id, investigation="replay continuity durability", status="active")


def test_continuity_decay_reduces_stale_confidence():
    fresh = apply_decay_to_confidence(base_confidence=0.8, age_hours=1.0)
    stale = apply_decay_to_confidence(base_confidence=0.8, age_hours=30.0)
    assert fresh > stale
    decay = compute_continuity_decay(age_hours=30.0)
    assert decay["stale"] is True


def test_thread_isolation_detects_conflation():
    isolation = score_thread_isolation(
        investigations=["Railway deployment", "replay continuity", "topology instability"],
        focus_topics=["deployment recovery"],
        primary_subject="Railway deployment",
    )
    assert isolation["conflated"] is True
    assert isolation["isolation_score"] < 0.55


def test_memory_precedence_reconciliation():
    _seed()
    reconciliation = reconcile_memory_layers(session_id="test-1172", channel="telegram")
    assert reconciliation["authoritative_source"] in {"active_investigation", "operational_context_store", "operational_memory"}
    assert reconciliation["primary_subject"] is not None


def test_investigation_lifecycle_snapshots():
    _seed()
    lifecycle = assess_investigation_lifecycle(session_id="test-1172")
    assert lifecycle["active_count"] >= 1
    assert lifecycle["lifecycle_managed"] is True


def test_operational_thread_integrity_aggregate():
    _seed()
    state = assess_operational_thread_integrity(session_id="test-1172", channel="telegram")
    assert state["phase"] == "11.7.2"
    assert state["ok"] is True
    assert "thread integrity" in state["summary"].lower()


def test_conversational_grounding_phase_1172():
    _seed()
    state = assess_conversational_operational_grounding(session_id="test-1172", channel="telegram")
    assert state["phase"] == "11.8.2"
    assert state["thread_integrity"] is not None
    assert (
        "semantic diversification" in state["narrative"].lower()
        or "thread integrity" in state["narrative"].lower()
        or "live provider" in state["narrative"].lower()
    )
