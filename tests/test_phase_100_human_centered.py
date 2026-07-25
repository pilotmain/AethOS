# SPDX-License-Identifier: Apache-2.0
"""Phase 10.0 — Human-centered agentic operating system."""

from __future__ import annotations

import pytest

from aethos_core.action_runtime.action_runtime import approve_action, clear_action_queue_for_tests, list_pending_actions, propose_action
from aethos_core.channels.universal.universal_channel_runtime import list_universal_channels, route_channel_inbound
from aethos_core.collaboration.collaboration_runtime import clear_collaboration_for_tests, start_collaboration_session
from aethos_core.human_centered.human_os_runtime import get_human_os_overview
from aethos_core.life.life_runtime import get_lifeos_status, opt_in_lifeos, revoke_lifeos
from aethos_core.relational.collaboration_modes import select_collaboration_mode
from aethos_core.relational.human_signal_detection import detect_human_signals
from aethos_core.relational.trust_memory import clear_trust_memory_for_tests
from aethos_core.trust.trust_leadership import build_trust_center
from aethos_core.voice.voice_governance import validate_voice_action


@pytest.fixture(autouse=True)
def _clean():
    clear_action_queue_for_tests()
    clear_collaboration_for_tests()
    clear_trust_memory_for_tests()
    yield
    clear_action_queue_for_tests()
    clear_collaboration_for_tests()
    clear_trust_memory_for_tests()


def test_human_signal_detection_frustration():
    signals = detect_human_signals("I'm frustrated — deployment failed again")
    assert signals.get("frustrated") is True
    assert "frustration" in (signals.get("signals") or [])


def test_crisis_mode_selection():
    mode = select_collaboration_mode("production down — customers affected")
    assert mode.get("mode") == "crisis"


def test_governed_action_blocks_forbidden():
    result = propose_action(action_type="purchase", session_id="test")
    assert result.get("ok") is False
    assert result.get("autonomous_execution_blocked") is True


def test_governed_action_requires_approval():
    result = propose_action(action_type="slack_post", session_id="test")
    assert result.get("ok") is True
    action = result.get("action") or {}
    assert action.get("status") == "pending_approval"
    approved = approve_action(action_id=str(action.get("action_id")), operator_id="op1")
    assert approved.get("ok") is True
    pending = list_pending_actions(session_id="test")
    assert pending.get("count") == 0


def test_voice_governance_blocks_silent_actions():
    gov = validate_voice_action(action_type="purchase")
    assert gov.get("ok") is False
    gov2 = validate_voice_action(action_type="slack_post", requires_approval=False)
    assert gov2.get("ok") is False


def test_lifeos_opt_in_revocable():
    status = get_lifeos_status(session_id="life-test")
    assert status.get("opted_in") is False
    opt_in_lifeos(session_id="life-test", domains=["calendar", "reminders"])
    assert get_lifeos_status(session_id="life-test").get("opted_in") is True
    revoke_lifeos(session_id="life-test")
    assert get_lifeos_status(session_id="life-test").get("opted_in") is False


def test_universal_channels_same_brain():
    channels = list_universal_channels()
    assert channels.get("ok") is True
    names = [c.get("name") for c in (channels.get("channels") or [])]
    assert "telegram" in names
    assert "slack" in names


def test_slack_inbound_routes_through_orchestration():
    result = route_channel_inbound(channel="slack", payload={"text": "hello", "user_id": "u1", "channel_id": "c1"})
    assert result.get("ok") is True
    assert result.get("reply")
    assert result.get("governance") == "same_brain_same_audit"


def test_collaboration_human_authoritative():
    collab = start_collaboration_session(operator_id="op1", focus="debug", context="test")
    session = collab.get("session") or {}
    assert session.get("human_authoritative") is True
    assert session.get("autonomous_execution_blocked") is True


def test_trust_center_safety_boundaries():
    trust = build_trust_center()
    boundaries = trust.get("safety_boundaries") or {}
    assert boundaries.get("autonomous_deploy_blocked") is True
    assert boundaries.get("silent_mutations_blocked") is True


def test_human_os_overview_convergence():
    overview = get_human_os_overview()
    assert overview.get("phase") == "10.0"
    assert overview.get("autonomous_execution_blocked") is True
    assert "relational" in overview
    assert "voice" in overview
    assert "channels" in overview
    assert "trust" in overview


def test_chat_relational_layer_applied():
    from aethos_core.chat.service import resolve_chat_turn

    result = resolve_chat_turn("companion mode please", session_id="rel-test")
    assert "companion" in result.reply.lower() or "mode" in result.reply.lower()
    assert result.meta.get("relational_mode") or result.meta.get("lane")


def test_relational_intelligence_away_brief():
    from aethos_core.chat.relational_intelligence import execute_relational_intelligence

    handled = execute_relational_intelligence("while you were away", session_id="away-test")
    assert handled is not None
    body, intent, meta = handled
    assert "away" in body.lower() or "operational" in body.lower()
    assert meta.get("autonomous_execution_blocked") == "true"
