# SPDX-License-Identifier: Apache-2.0
"""Governance presence — contextual, trust-oriented governance phrasing."""

from __future__ import annotations

from typing import Any

from aethos_core.identity.trust_language import EXECUTION_TRUST_REMINDER, LIGHT_TRUST_REMINDER
from aethos_core.relational.presence_timing import should_skip_governance_footer

_NO_GOVERNANCE_INTENTS = frozenset({
    "greeting",
    "casual_greeting",
    "capability_intro",
    "capability_response",
    "platform_identity_response",
    "creator_attribution_response",
    "human_support_response",
    "general_help",
    "conversation_resume",
    "live_presence_nudge",
    "operational_copilot",
    "relational_state",
    "living_intelligence",
    "ambient_presence",
    "operational_presence",
    "generative_answer",
    "identity_intro",
})

_STRONG_GOVERNANCE_INTENTS = frozenset({
    "mutation_preflight",
    "operation_preflight",
    "tracked_job",
    "queued_tracked_job",
    "browser_evidence",
    "external_site_task",
    "action_status",
})


def governance_visibility(
    *,
    intent: str | None = None,
    lane: str | None = None,
    mode: str = "companion",
) -> str:
    if should_skip_governance_footer(intent=intent, lane=lane):
        return "none"
    if intent in _NO_GOVERNANCE_INTENTS:
        return "none"
    if mode == "executive":
        return "none"
    if intent in _STRONG_GOVERNANCE_INTENTS:
        return "strong"
    if intent in {"runtime_status", "runtime_config_query", "setup", "clarification"}:
        return "implicit"
    if intent == "capability_question":
        return "implicit"
    if intent in {"vercel_readonly", "github_readonly", "railway_readonly", "provider_job"}:
        return "explicit"
    return "lightweight"


def governance_phrase(
    *,
    intent: str | None = None,
    lane: str | None = None,
    mode: str = "companion",
) -> str | None:
    level = governance_visibility(intent=intent, lane=lane, mode=mode)
    if level in {"none", "implicit"}:
        return None
    if level == "strong":
        return EXECUTION_TRUST_REMINDER
    return LIGHT_TRUST_REMINDER


def apply_contextual_governance(
    text: str,
    *,
    intent: str | None = None,
    lane: str | None = None,
    emotional_context: dict[str, Any] | None = None,
    include_governance: bool = True,
) -> str:
    if not include_governance:
        return text
    mode = ((emotional_context or {}).get("mode") or {}).get("mode") or "companion"
    lower = text.lower()
    if "governance" in lower or "approval-gated" in lower or "human-authorized" in lower:
        return text
    phrase = governance_phrase(intent=intent, lane=lane, mode=mode)
    if not phrase:
        return text
    return f"{text.rstrip()}\n\n*{phrase}*"
