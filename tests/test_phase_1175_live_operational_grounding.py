# SPDX-License-Identifier: Apache-2.0
"""Phase 11.7.5 — Live operational grounding tests."""

from __future__ import annotations

from aethos_core.conversation.legacy_polish_api import synthesize_grounded_operational_reply
from aethos_core.conversation.legacy_polish_api import assess_conversational_operational_grounding
from aethos_core.conversation.operational_memory import clear_operational_memory_for_tests, persist_investigation, record_focus_recovery
from aethos_core.human_centered.continuity_memory import clear_continuity_memory_for_tests, set_active_phase
from aethos_core.live_operational_grounding.grounding_runtime import orchestrate_live_grounding
from aethos_core.live_operational_grounding.live_operation_harness import list_live_operation_flows, run_live_operation_flow
from aethos_core.live_operational_grounding.live_narrative_composer import compose_live_stability_reply
from aethos_core.live_operational_grounding.provider_signal_binding import bind_provider_signals
from aethos_core.live_operational_grounding.regression_guardrails import assess_regression_guardrails
from aethos_core.live_operational_grounding.runtime import assess_live_operational_grounding
from aethos_core.live_operational_grounding.signal_freshness_tracking import track_signal_freshness
from aethos_core.operational_context_memory.context_store import persist_operational_context
from aethos_core.operational_truth.capability_truth_matrix import build_capability_truth_matrix


def _seed(session_id: str = "test-1175") -> None:
    clear_operational_memory_for_tests()
    clear_continuity_memory_for_tests()
    subject = "Railway deployment recovery"
    record_focus_recovery(session_id=session_id, focus=subject, channel="telegram")
    persist_investigation(session_id=session_id, investigation="replay continuity durability")
    persist_operational_context(
        session_id=session_id,
        context={"deployment_subject": subject, "latest_investigation": "replay continuity durability"},
    )
    set_active_phase(session_id=session_id, phase="recovery", focus=subject)


def test_provider_signal_binding_railway():
    binding = bind_provider_signals(primary_subject="Railway deployment recovery", category="recovery")
    assert binding["bound"] is True
    assert binding["provider"] == "railway"
    assert binding["runtime_signals"]["fully_proven"] is False


def test_signal_freshness_tracks_sources():
    _seed()
    freshness = track_signal_freshness(session_id="test-1175", channel="telegram")
    assert freshness["signals_fresh"] is True
    assert "operational_context" in freshness["sources"]


def test_live_operation_harness_flows():
    flows = list_live_operation_flows()
    assert any(f["id"] == "railway_restart" for f in flows)
    result = run_live_operation_flow(flow_id="railway_restart")
    assert result["ok"] is True
    assert "verification" in result


def test_regression_guardrails_block_fake_execution():
    bad = assess_regression_guardrails(reply="I executed the restart for you.", grounded=True)
    assert bad["guardrails_qualified"] is False
    good = assess_regression_guardrails(
        reply="The Railway restart appears to be holding so far.",
        grounded=True,
    )
    assert good["guardrails_qualified"] is True


def test_live_stability_narrative_avoids_fully_proven():
    live = orchestrate_live_grounding(session_id="test-1175", channel="telegram", primary_subject="Railway deployment recovery")
    reply = compose_live_stability_reply(
        subject="Railway deployment recovery",
        live=live["live_reality"],
        closing="Still watching.",
        intent="did_it_hold",
    )
    assert "fully proven" in reply.lower() or "stabilizing" in reply.lower()
    assert "fully resolved" not in reply.lower()


def test_synthesis_live_follow_up():
    _seed()
    result = synthesize_grounded_operational_reply(
        user_text="Did it hold?",
        session_id="test-1175",
        channel="telegram",
    )
    assert result is not None
    assert result["live_grounding"] is not None
    assert "approval-gated" not in result["reply"].lower()
    assert result["regression_guardrails"]["guardrails_qualified"] is True


def test_live_operational_grounding_aggregate():
    _seed()
    state = assess_live_operational_grounding(session_id="test-1175", channel="telegram")
    assert state["phase"] == "11.7.5"
    assert state["live_operational_grounding"]["provider_binding"]["bound"] is True


def test_conversational_grounding_phase_1175():
    _seed()
    state = assess_conversational_operational_grounding(session_id="test-1175", channel="telegram")
    assert state["phase"] == "11.8.2"
    assert state["live_operational_grounding"] is not None
    assert "live provider" in state["narrative"].lower()


def test_recovery_verification_windows_block_premature_stable():
    from aethos_core.live_operational_grounding.recovery_verification_windows import assess_recovery_verification_windows
    from time import time

    recent = assess_recovery_verification_windows(
        session_id="test-1175",
        operation_started_at=time() - 120,  # 2 minutes ago
        provider_converged=True,
    )
    assert recent["premature_stable_blocked"] is True
    assert recent["current_window"] == "immediate"

    sustained = assess_recovery_verification_windows(
        session_id="test-1175",
        operation_started_at=time() - 1200,  # 20 minutes ago
        provider_converged=True,
    )
    assert sustained["fully_proven"] is True


def test_capability_matrix_live_operational_grounding():
    matrix = build_capability_truth_matrix()
    entry = next((r for r in matrix if r.get("id") == "live_operational_grounding"), None)
    assert entry is not None and entry["verification_coverage_pct"] >= 89
