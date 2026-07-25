# SPDX-License-Identifier: Apache-2.0
"""Conversational restraint — prevent repetitive identity and governance spam."""

from __future__ import annotations

from aethos_core.relational.conversational_memory import recent_context

_GOVERNANCE_MARKERS = (
    "approval-gated",
    "human-authorized",
    "governed assistance",
    "you approve and execute",
)


def recent_assistant_mentions_governance(session_id: str = "default", limit: int = 3) -> bool:
    for turn in recent_context(session_id=session_id, limit=limit):
        if turn.get("role") != "assistant":
            continue
        summary = (turn.get("summary") or "").lower()
        if any(marker in summary for marker in _GOVERNANCE_MARKERS):
            return True
    return False


def should_suppress_governance_footer(*, intent: str | None, session_id: str = "default") -> bool:
    if intent in {
        "greeting",
        "casual_greeting",
        "capability_question",
        "capability_intro",
        "capability_response",
        "platform_identity_response",
        "creator_attribution_response",
        "human_support_response",
        "general_help",
        "identity_intro",
        "generative_answer",
        "railway_deploy_capability_truth",
        "vercel_deploy_capability_truth",
        "railway_e2e_missing_config",
        "vercel_e2e_missing_config",
        "railway_e2e_readiness_blocked",
        "provider_e2e_readiness_report",
        "execution_brain_railway_pilot",
        "execution_brain_preflight_created",
        "execution_brain_recovery",
        "github_delivery_capability_truth",
    }:
        return True
    return recent_assistant_mentions_governance(session_id=session_id)


def should_suppress_confidence_suffix(*, intent: str | None, text: str) -> bool:
    if intent in {"greeting", "capability_question", "identity_intro", "conversation_resume"}:
        return True
    return "confidence" in text.lower()
