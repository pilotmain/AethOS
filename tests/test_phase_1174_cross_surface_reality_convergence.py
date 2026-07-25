# SPDX-License-Identifier: Apache-2.0
"""Phase 11.7.4 — Cross-surface reality convergence tests."""

from __future__ import annotations

from aethos_core.conversation.legacy_polish_api import assess_conversational_operational_grounding
from aethos_core.cross_surface_reality_convergence.convergence_runtime import orchestrate_cross_surface_convergence
from aethos_core.cross_surface_reality_convergence.reality_drift_detection import detect_reality_drift
from aethos_core.cross_surface_reality_convergence.runtime import assess_cross_surface_reality_convergence
from aethos_core.cross_surface_reality_convergence.surface_alignment import extract_surface_subjects, score_surface_alignment
from aethos_core.conversation.operational_memory import clear_operational_memory_for_tests, persist_investigation, record_focus_recovery
from aethos_core.human_centered.continuity_memory import clear_continuity_memory_for_tests, set_active_phase
from aethos_core.operational_context_memory.context_store import persist_operational_context
from aethos_core.operational_truth.capability_truth_matrix import build_capability_truth_matrix


def _seed_aligned(session_id: str = "test-1174") -> None:
    clear_operational_memory_for_tests()
    clear_continuity_memory_for_tests()
    subject = "Railway deployment recovery"
    record_focus_recovery(session_id=session_id, focus=subject, channel="telegram")
    persist_investigation(session_id=session_id, investigation="replay continuity durability")
    persist_operational_context(
        session_id=session_id,
        context={
            "deployment_subject": subject,
            "latest_investigation": "replay continuity durability",
        },
    )
    set_active_phase(session_id=session_id, phase="recovery", focus=subject)


def _seed_drift(session_id: str = "test-1174-drift") -> None:
    clear_operational_memory_for_tests()
    clear_continuity_memory_for_tests()
    record_focus_recovery(session_id=session_id, focus="Railway deployment recovery", channel="telegram")
    persist_operational_context(
        session_id=session_id,
        context={"deployment_subject": "topology dependency instability"},
    )
    set_active_phase(session_id=session_id, phase="topology", focus="Kubernetes rollout verification")


def test_surface_alignment_detects_aligned_subjects():
    _seed_aligned("test-1174-align")
    subjects = extract_surface_subjects(session_id="test-1174-align", channel="telegram")
    alignment = score_surface_alignment(surface_subjects=subjects)
    assert alignment["surfaces_aligned"] is True
    assert alignment["alignment_score"] >= 0.55


def test_surface_alignment_detects_drift():
    _seed_drift()
    subjects = extract_surface_subjects(session_id="test-1174-drift", channel="telegram")
    alignment = score_surface_alignment(surface_subjects=subjects)
    drift = detect_reality_drift(alignment=alignment, bridge={"surfaces": ["mission_control", "telegram"]})
    assert alignment["surfaces_aligned"] is False
    assert drift["drift_detected"] is True


def test_cross_surface_convergence_aggregate():
    _seed_aligned()
    state = assess_cross_surface_reality_convergence(session_id="test-1174", channel="telegram")
    assert state["phase"] == "11.7.4"
    assert state["ok"] is True
    convergence = state["cross_surface_convergence"]
    assert convergence["convergence_qualified"] is True


def test_orchestrate_cross_surface_convergence_drift_fails_gate():
    _seed_drift()
    convergence = orchestrate_cross_surface_convergence(session_id="test-1174-drift", channel="telegram")
    assert convergence["drift_detected"] is True
    assert convergence["convergence_qualified"] is False


def test_conversational_grounding_phase_1174():
    _seed_aligned()
    state = assess_conversational_operational_grounding(session_id="test-1174", channel="telegram")
    assert state["phase"] == "11.8.2"
    assert state["cross_surface_convergence"] is not None
    assert "cross-surface" in state["narrative"].lower() or "live provider" in state["narrative"].lower()


def test_capability_matrix_cross_surface_reality_convergence():
    matrix = build_capability_truth_matrix()
    entry = next((r for r in matrix if r.get("id") == "cross_surface_reality_convergence"), None)
    assert entry is not None and entry["verification_coverage_pct"] >= 89
