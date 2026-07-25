# SPDX-License-Identifier: Apache-2.0
"""FIX 316D — continuity reports and drift detection."""

from __future__ import annotations

import re
from typing import Any

from aethos_core.conversation.continuity_pkg.conversation_continuity_store import get_session_state
from aethos_core.conversation.continuity_pkg.conversation_continuity_topic_classifier import (
    topic_in_human_support,
    topic_in_identity,
    topic_in_operational,
)

MEMORY_LOSS_RX = re.compile(
    r"\b(?:i\s+)?(?:don't|do not)\s+remember\b|\bno memory of\b|\bfresh conversation\b|\bnew conversation\b",
    re.I,
)


def build_active_topic_registry(*, session_id: str) -> dict[str, Any]:
    state = get_session_state(session_id=session_id)
    return {
        "current_topic": state.get("active_topic"),
        "parent_topic": state.get("parent_topic"),
        "confidence": state.get("confidence"),
        "active_mode": state.get("active_mode"),
        "turn_count": state.get("turn_count"),
        "last_classification": state.get("last_classification"),
    }


def build_human_support_continuity_report(*, session_id: str) -> dict[str, Any]:
    state = get_session_state(session_id=session_id)
    active = topic_in_human_support(state.get("active_topic")) or state.get("active_mode") == "human_support"
    return {
        "human_support_active": active,
        "active_topic": state.get("active_topic"),
        "follow_up_persistence_enabled": active,
        "operational_switch_forbidden_while_active": active,
    }


def build_operational_continuity_report(*, session_id: str) -> dict[str, Any]:
    state = get_session_state(session_id=session_id)
    active = topic_in_operational(state.get("active_topic")) or state.get("active_mode") == "operational"
    return {
        "operational_context_active": active,
        "active_topic": state.get("active_topic"),
        "mode_persistence_enabled": active,
    }


def detect_topic_drift(
    *,
    session_id: str,
    classification: str | None,
    response_kind: str | None,
) -> dict[str, Any]:
    state = get_session_state(session_id=session_id)
    findings: list[dict[str, str]] = []
    active_mode = state.get("active_mode")
    active_topic = state.get("active_topic")
    kind = response_kind or classification or ""

    if active_mode == "human_support" and kind in {
        "capability_response",
        "provider_support_response",
        "operational_action",
    }:
        findings.append(
            {
                "kind": "operational_advice_inside_emotional_support",
                "detail": "Human-support topic active but response shifted to operational mode.",
            }
        )

    if active_mode == "operational" and kind == "human_support_response":
        findings.append(
            {
                "kind": "emotional_advice_inside_operational_workflow",
                "detail": "Operational topic active but response shifted to human-support mode.",
            }
        )

    if active_mode == "identity" and kind in {"provider_support_response", "capability_response"}:
        findings.append(
            {
                "kind": "capability_or_provider_report_inside_identity_discussion",
                "detail": "Identity topic active but response shifted away from identity context.",
            }
        )

    if active_topic and state.get("last_classification") and classification != state.get("last_classification"):
        if kind == "capability_response" and topic_in_identity(active_topic):
            findings.append(
                {
                    "kind": "capability_report_inside_identity_discussion",
                    "detail": "Follow-up lost identity topic to capability summary.",
                }
            )

    return {
        "findings": findings,
        "drift_detected": bool(findings),
        "active_topic": active_topic,
        "active_mode": active_mode,
    }


def validate_memory_truth(*, answer_text: str, session_id: str) -> dict[str, Any]:
    state = get_session_state(session_id=session_id)
    turn_count = int(state.get("turn_count") or 0)
    text = answer_text or ""
    matches = [match.group(0) for match in MEMORY_LOSS_RX.finditer(text)]
    context_exists = turn_count > 0 or bool(state.get("active_topic"))
    invalid = context_exists and bool(matches)
    return {
        "context_exists": context_exists,
        "false_memory_loss_detected": invalid,
        "matches": matches,
        "valid": not invalid,
        "turn_count": turn_count,
        "active_topic": state.get("active_topic"),
    }


def build_conversation_recovery_report(
    *,
    session_id: str,
    drift_report: dict[str, Any],
) -> dict[str, Any]:
    state = get_session_state(session_id=session_id)
    if not drift_report.get("drift_detected"):
        return {
            "recovery_required": False,
            "active_topic": state.get("active_topic"),
        }
    return {
        "recovery_required": True,
        "active_topic": state.get("active_topic"),
        "active_mode": state.get("active_mode"),
        "findings": drift_report.get("findings") or [],
        "recovery_action": "acknowledge_drift_and_return_to_active_topic",
    }


def sanitize_memory_truth(*, answer_text: str, session_id: str) -> tuple[str, dict[str, Any]]:
    report = validate_memory_truth(answer_text=answer_text, session_id=session_id)
    if not report["false_memory_loss_detected"]:
        return answer_text, report

    cleaned = MEMORY_LOSS_RX.sub("", answer_text)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()
    topic = report.get("active_topic") or "our current topic"
    prefix = f"We're still in the same session, continuing **{topic}**. "
    if cleaned:
        return prefix + cleaned, report
    return prefix + "I'm here with you.", report
