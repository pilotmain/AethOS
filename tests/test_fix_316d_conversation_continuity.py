# SPDX-License-Identifier: Apache-2.0
"""FIX 316D — conversation continuity tests."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from aethos_core.conversation.continuity_pkg.conversation_continuity_contract import (
    AUTHORITY_FLAGS,
    CONVERSATION_CONTINUITY_DOMAINS,
)
from aethos_core.conversation.continuity_pkg.conversation_continuity_evaluator import (
    detect_topic_drift,
    sanitize_memory_truth,
    validate_memory_truth,
)
from aethos_core.conversation.continuity_pkg.conversation_continuity_follow_up import resolve_follow_up_intent
from aethos_core.conversation.continuity_pkg.conversation_continuity_service import build_conversation_continuity
from aethos_core.conversation.continuity_pkg.conversation_continuity_store import (
    clear_continuity_review_records_for_tests,
    clear_session_state_for_tests,
    get_session_state,
    update_session_state,
)
from aethos_core.conversation.continuity_pkg.conversation_continuity_topic_classifier import is_follow_up_prompt
from aethos_core.identity_truth_lock.identity_truth_lock_contract import PLATFORM_CREATOR
from aethos_core.runtime_truth_alignment.runtime_truth_alignment_router import route_runtime_truth_alignment

_MOCK_EVIDENCE = {
    "session_id": "cc-316d",
    "sources_ok": {"fix_316b": True, "fix_295": True, "fix_296": True, "fix_303": True},
    "capability_summary": {
        "proven_items": ["Mission Control (PROVEN)"],
        "operational_items": ["Provider inspection (OPERATIONAL)"],
        "planned_items": [],
        "experimental_items": [],
        "maturity_tier": "OPERATIONAL",
    },
    "provider_summary": {
        "phase_1_providers": ["GitHub", "Railway", "Vercel"],
        "phase_2_providers": ["AWS"],
        "connected_provider_count": 1,
        "provider_reports": [],
    },
    "readiness_summary": {"overall_launch_status": "CONDITIONAL", "blockers": []},
    "identity_truth_lock": {
        "sections": {"identity_truth_validation_report": {"overall_ok": True, "checks": {}}}
    },
    "trust_report_freezes": {},
}


@pytest.fixture(autouse=True)
def _clean_continuity_state():
    clear_session_state_for_tests()
    clear_continuity_review_records_for_tests()
    yield
    clear_session_state_for_tests()
    clear_continuity_review_records_for_tests()


@pytest.fixture(autouse=True)
def _mock_truth_evidence():
    with patch(
        "aethos_core.truth_consistency.truth_consistency_responses.collect_truth_evidence_lightweight",
        return_value=_MOCK_EVIDENCE,
    ), patch(
        "aethos_core.identity_truth_lock.identity_truth_lock_responses._safe_capability_evidence",
        return_value={
            "proven_items": ["Mission Control (PROVEN)"],
            "operational_items": ["Provider inspection (OPERATIONAL)"],
            "authority_note": "Observation only.",
            "provider_readiness": [],
            "maturity_tier": "OPERATIONAL",
        },
    ), patch(
        "aethos_core.runtime_truth_alignment.runtime_truth_alignment_composer._safe_capability_evidence",
        return_value={
            "proven_items": ["Mission Control (PROVEN)"],
            "operational_items": ["Provider inspection (OPERATIONAL)"],
            "authority_note": "Observation only.",
            "provider_readiness": [],
            "maturity_tier": "OPERATIONAL",
        },
    ):
        yield


def test_conversation_continuity_domains_and_authority_flags():
    result = build_conversation_continuity(session_id="cc-316d")
    assert list(CONVERSATION_CONTINUITY_DOMAINS) == list(result.sections.keys())
    assert AUTHORITY_FLAGS["conversation_authority"] is False
    assert AUTHORITY_FLAGS["automatic_memory_creation_enabled"] is False


def test_depression_continuity_regression():
    first = route_runtime_truth_alignment("I'm depressed", session_id="cc-316d-dep")
    assert first is not None
    assert first[1] == "human_support_response"
    assert get_session_state(session_id="cc-316d-dep")["active_mode"] == "human_support"

    follow_up = route_runtime_truth_alignment("What other advice do you have?", session_id="cc-316d-dep")
    assert follow_up is not None
    assert follow_up[1] == "human_support_follow_up_response"
    assert "Continuing" in follow_up[0]
    assert "Mission Control" not in follow_up[0]
    assert "What I can do" not in follow_up[0]


def test_identity_continuity_regression():
    first = route_runtime_truth_alignment("Who created AethOS?", session_id="cc-316d-id")
    assert first is not None
    assert PLATFORM_CREATOR in first[0]

    shifted = route_runtime_truth_alignment("What about Claude?", session_id="cc-316d-id")
    assert shifted is not None
    assert "Anthropic" in shifted[0]
    assert PLATFORM_CREATOR not in shifted[0]


def test_follow_up_resolution_regression():
    update_session_state(
        session_id="cc-316d-follow",
        active_topic="platform_identity",
        parent_topic="identity",
        active_mode="identity",
        last_classification="platform_identity_response",
        confidence=0.9,
    )
    assert is_follow_up_prompt("Tell me more")
    resolved = resolve_follow_up_intent(text="Tell me more", session_id="cc-316d-follow")
    assert resolved["resolved"] is True
    assert resolved["classification"] == "platform_identity_response"


def test_memory_truth_regression():
    update_session_state(
        session_id="cc-316d-mem",
        active_topic="depression",
        active_mode="human_support",
        increment_turn=True,
    )
    report = validate_memory_truth(
        answer_text="I don't remember our conversation.",
        session_id="cc-316d-mem",
    )
    assert report["false_memory_loss_detected"] is True

    cleaned, _ = sanitize_memory_truth(
        answer_text="I don't remember our conversation.",
        session_id="cc-316d-mem",
    )
    assert "don't remember" not in cleaned.lower()
    assert "same session" in cleaned.lower()


def test_topic_drift_regression():
    update_session_state(
        session_id="cc-316d-drift",
        active_topic="depression",
        active_mode="human_support",
        last_classification="human_support_response",
    )
    drift = detect_topic_drift(
        session_id="cc-316d-drift",
        classification="capability_response",
        response_kind="capability_response",
    )
    assert drift["drift_detected"] is True


def test_conversation_recovery_regression():
    first = route_runtime_truth_alignment("I feel depressed", session_id="cc-316d-recover")
    assert first is not None
    update_session_state(
        session_id="cc-316d-recover",
        active_topic="depression",
        active_mode="human_support",
        last_classification="human_support_response",
    )
    follow_up = route_runtime_truth_alignment("Tell me more", session_id="cc-316d-recover")
    assert follow_up is not None
    assert follow_up[2]["memory_truth_valid"] == "true"


def test_operational_continuity_regression():
    update_session_state(
        session_id="cc-316d-ops",
        active_topic="deployment",
        parent_topic="operational",
        active_mode="operational",
        last_classification="operational_action",
        confidence=0.9,
    )
    resolved = resolve_follow_up_intent(text="Tell me more", session_id="cc-316d-ops")
    assert resolved["resolved"] is True
    assert resolved["continue_operational_lane"] is True
