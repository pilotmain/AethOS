# SPDX-License-Identifier: Apache-2.0
"""Restraint runtime — contextual governance suppression orchestration."""

from __future__ import annotations

from typing import Any

_INFORMATIONAL_INTENTS = frozenset({
    "situation_improved",
    "deployment_stabilized",
    "recovery_status",
    "what_changed",
    "did_it_hold",
    "monitoring_advice",
    "operational_status",
    "implicit_followup",
    "generative_answer",
    "conversation_resume",
    "operational_copilot",
    "greeting",
    "casual_greeting",
    "capability_question",
    "capability_intro",
    "capability_response",
    "platform_identity_response",
    "creator_attribution_response",
    "human_support_response",
    "general_help",
    "clarification",
    "agent_creation",
    "entity_status",
    "workspace_results",
    "agent_conclusion",
    "completion_watch",
    "job_status",
    "progress_inquiry",
    "identity_intro",
})


def assess_governance_restraint(
    *,
    intent: str | None = None,
    lane: str | None = None,
    channel: str = "chat",
    grounded: bool = False,
    suppress_governance_footer: bool = False,
) -> dict[str, Any]:
    suppress = suppress_governance_footer or intent in _INFORMATIONAL_INTENTS or grounded or lane in {
        "operational_grounding",
        "operational_entity",
        "operational_progression",
        "conversational_execution",
        "living_intelligence",
        "relational_intelligence",
        "presence_intelligence",
    }
    if channel == "telegram" and intent in _INFORMATIONAL_INTENTS:
        suppress = True
    visibility = "none" if suppress else "lightweight"
    return {
        "suppress_footer": suppress,
        "visibility": visibility,
        "summary": "Governance restrained for conversational operational grounding." if suppress else "Governance visibility evaluated.",
    }


def apply_governance_restraint(
    text: str,
    *,
    intent: str | None = None,
    lane: str | None = None,
    channel: str = "chat",
    emotional_context: dict[str, Any] | None = None,
    grounded: bool = False,
    suppress_governance_footer: bool = False,
) -> str:
    restraint = assess_governance_restraint(
        intent=intent,
        lane=lane,
        channel=channel,
        grounded=grounded,
        suppress_governance_footer=suppress_governance_footer,
    )
    if restraint.get("suppress_footer"):
        return text
    from aethos_core.identity.governance_presence import apply_contextual_governance

    return apply_contextual_governance(
        text,
        intent=intent,
        lane=lane,
        emotional_context=emotional_context,
        include_governance=True,
    )
