# SPDX-License-Identifier: Apache-2.0
"""FIX 316D — conversation continuity service."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from aethos_core.conversation.continuity_pkg.conversation_continuity_contract import (
    AUTHORITY_FLAGS,
    CONVERSATION_CONTINUITY_DOMAINS,
    CONVERSATION_CONTINUITY_FIX,
)
from aethos_core.conversation.continuity_pkg.conversation_continuity_evaluator import (
    build_active_topic_registry,
    build_conversation_recovery_report,
    build_human_support_continuity_report,
    build_operational_continuity_report,
    detect_topic_drift,
    validate_memory_truth,
)
from aethos_core.conversation.continuity_pkg.conversation_continuity_follow_up import resolve_follow_up_intent
from aethos_core.conversation.continuity_pkg.conversation_continuity_store import (
    get_session_state,
    list_continuity_review_records,
)


@dataclass(frozen=True)
class ConversationContinuityResult:
    conversation_continuity: dict[str, Any]

    @property
    def sections(self) -> dict[str, Any]:
        return self.conversation_continuity.get("sections") or {}


def build_conversation_continuity(
    *,
    session_id: str = "default",
    sample_text: str = "",
    sample_classification: str | None = None,
    sample_response_kind: str | None = None,
) -> ConversationContinuityResult:
    sid = (session_id or "default").strip()[:64] or "default"
    state = get_session_state(session_id=sid)

    active_topic_registry = build_active_topic_registry(session_id=sid)
    follow_up_resolution_report = resolve_follow_up_intent(text=sample_text, session_id=sid)
    human_support_continuity_report = build_human_support_continuity_report(session_id=sid)
    operational_continuity_report = build_operational_continuity_report(session_id=sid)
    topic_drift_report = detect_topic_drift(
        session_id=sid,
        classification=sample_classification,
        response_kind=sample_response_kind,
    )
    memory_truth_report = validate_memory_truth(answer_text="", session_id=sid)
    conversation_recovery_report = build_conversation_recovery_report(
        session_id=sid,
        drift_report=topic_drift_report,
    )
    continuity_dashboard = {
        "active_topic": state.get("active_topic"),
        "parent_topic": state.get("parent_topic"),
        "active_mode": state.get("active_mode"),
        "turn_count": state.get("turn_count"),
        "human_support_persistence": human_support_continuity_report.get("follow_up_persistence_enabled"),
        "operational_persistence": operational_continuity_report.get("mode_persistence_enabled"),
        "topic_drift_detected": topic_drift_report.get("drift_detected"),
        "authority_flags": dict(AUTHORITY_FLAGS),
        "core_principle": "conversation_context ≠ long_term_memory",
    }
    continuity_review_registry = {
        "records": list_continuity_review_records(),
        "commands": (
            "continuity note: ...",
            "continuity review approve|hold|reject|defer: ...",
        ),
        "record_only": True,
    }
    session_truth_registry = {
        "session_id": sid,
        "active_conversation": state.get("turn_count", 0) > 0,
        "active_topic": state.get("active_topic"),
        "active_mode": state.get("active_mode"),
        "last_intent": state.get("last_intent"),
        "conversation_context_is_session_scoped": True,
        "long_term_memory_required": False,
    }

    sections = {
        "active_topic_registry": active_topic_registry,
        "follow_up_resolution_report": follow_up_resolution_report,
        "human_support_continuity_report": human_support_continuity_report,
        "operational_continuity_report": operational_continuity_report,
        "topic_drift_report": topic_drift_report,
        "memory_truth_report": memory_truth_report,
        "conversation_recovery_report": conversation_recovery_report,
        "continuity_dashboard": continuity_dashboard,
        "continuity_review_registry": continuity_review_registry,
        "session_truth_registry": session_truth_registry,
    }

    return ConversationContinuityResult(
        conversation_continuity={
            "fix": CONVERSATION_CONTINUITY_FIX,
            "session_id": sid,
            "domains": list(CONVERSATION_CONTINUITY_DOMAINS),
            "sections": sections,
        }
    )
