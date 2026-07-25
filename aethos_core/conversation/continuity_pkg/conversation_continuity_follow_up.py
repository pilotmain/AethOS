# SPDX-License-Identifier: Apache-2.0
"""FIX 316D — follow-up intent resolution."""

from __future__ import annotations

from typing import Any

from aethos_core.conversation.continuity_pkg.conversation_continuity_store import get_session_state
from aethos_core.conversation.continuity_pkg.conversation_continuity_topic_classifier import (
    detect_topic_shift,
    is_follow_up_prompt,
    topic_in_human_support,
    topic_in_identity,
    topic_in_operational,
)
from aethos_core.runtime_truth_alignment.runtime_truth_alignment_classifier import classify_runtime_prompt


def resolve_follow_up_intent(*, text: str, session_id: str) -> dict[str, Any]:
    raw = (text or "").strip()
    state = get_session_state(session_id=session_id)
    shift = detect_topic_shift(raw)
    if shift:
        return {
            "resolved": True,
            "resolution_kind": "topic_shift",
            "classification": shift.get("classification_hint"),
            "active_topic": shift.get("topic"),
            "parent_topic": shift.get("parent_topic"),
            "mode": shift.get("mode"),
            "confidence": shift.get("confidence", 0.95),
        }

    if not is_follow_up_prompt(raw):
        return {"resolved": False, "reason": "not_follow_up_prompt"}

    last_classification = state.get("last_classification")
    active_topic = state.get("active_topic")
    active_mode = state.get("active_mode")
    if not last_classification and not active_topic:
        return {"resolved": False, "reason": "no_active_topic"}

    if topic_in_human_support(active_topic) or active_mode == "human_support":
        return {
            "resolved": True,
            "resolution_kind": "human_support_follow_up",
            "classification": "human_support_follow_up_response",
            "active_topic": active_topic or "human_support",
            "parent_topic": state.get("parent_topic") or "human_support",
            "mode": "human_support",
            "confidence": 0.93,
        }

    if topic_in_identity(active_topic) or active_mode == "identity":
        classification = last_classification or "platform_identity_response"
        if classification.startswith("model_creator"):
            classification = last_classification or "creator_attribution_response"
        return {
            "resolved": True,
            "resolution_kind": "identity_follow_up",
            "classification": classification,
            "active_topic": active_topic or "platform_identity",
            "parent_topic": state.get("parent_topic") or "identity",
            "mode": "identity",
            "confidence": 0.9,
        }

    if topic_in_operational(active_topic) or active_mode == "operational":
        return {
            "resolved": True,
            "resolution_kind": "operational_follow_up",
            "classification": "operational_action",
            "active_topic": active_topic or "operational",
            "parent_topic": state.get("parent_topic") or "operational",
            "mode": "operational",
            "confidence": 0.88,
            "continue_operational_lane": True,
        }

    return {
        "resolved": True,
        "resolution_kind": "topic_follow_up",
        "classification": last_classification or classify_runtime_prompt(raw),
        "active_topic": active_topic,
        "parent_topic": state.get("parent_topic"),
        "mode": active_mode or "general",
        "confidence": 0.75,
    }


def should_persist_human_support_mode(*, text: str, session_id: str) -> bool:
    state = get_session_state(session_id=session_id)
    if state.get("active_mode") != "human_support" and not topic_in_human_support(state.get("active_topic")):
        return False
    if detect_topic_shift(text):
        return False
    direct = classify_runtime_prompt(text)
    if direct == "human_support_response":
        return True
    if direct in {"operational_action", "capability_response", "provider_support_response"}:
        return False
    if is_follow_up_prompt(text):
        return True
    if direct is None and len((text or "").split()) <= 8:
        return True
    return False
