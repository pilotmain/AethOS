# SPDX-License-Identifier: Apache-2.0
"""FIX 316D — conversation continuity contract."""

from __future__ import annotations

from typing import Final

CONVERSATION_CONTINUITY_FIX: Final[str] = "FIX 316D"
CONVERSATION_CONTINUITY_ROUTE_ID: Final[str] = "conversation_continuity"

CONVERSATION_CONTINUITY_DOMAINS: Final[tuple[str, ...]] = (
    "active_topic_registry",
    "follow_up_resolution_report",
    "human_support_continuity_report",
    "operational_continuity_report",
    "topic_drift_report",
    "memory_truth_report",
    "conversation_recovery_report",
    "continuity_dashboard",
    "continuity_review_registry",
    "session_truth_registry",
)

AUTHORITY_FLAGS: Final[dict[str, bool]] = {
    "conversation_authority": False,
    "automatic_memory_creation_enabled": False,
    "topic_mutation_authority": False,
}

FORBIDDEN_CONTINUITY_ACTIONS: Final[tuple[str, ...]] = (
    "claiming_memory_loss_when_context_exists",
    "switching_emotional_support_into_operational_advice",
    "switching_identity_discussions_into_provider_reports",
    "losing_active_topic_during_follow_up_questions",
)

HUMAN_SUPPORT_TOPICS: Final[frozenset[str]] = frozenset({
    "depression",
    "anxiety",
    "stress",
    "loneliness",
    "burnout",
})

OPERATIONAL_TOPICS: Final[frozenset[str]] = frozenset({
    "deployment",
    "rollback",
    "provider",
    "workflow",
})

IDENTITY_TOPICS: Final[frozenset[str]] = frozenset({
    "platform_identity",
    "creator_attribution",
    "ownership",
    "model_creator",
})

ECOSYSTEM_TOPICS: Final[frozenset[str]] = frozenset({
    "pilotos",
    "atlas",
    "nexora",
})

CONTINUITY_MODES: Final[frozenset[str]] = frozenset({
    "human_support",
    "operational",
    "identity",
    "capability",
    "ecosystem",
    "general",
})

CONTINUITY_REVIEW_DECISION_KINDS: Final[frozenset[str]] = frozenset({
    "continuity_review_decision_approve",
    "continuity_review_decision_hold",
    "continuity_review_decision_reject",
    "continuity_review_decision_defer",
})

CONTINUITY_REVIEW_RECORD_KINDS: Final[frozenset[str]] = frozenset({
    "continuity_note",
    *CONTINUITY_REVIEW_DECISION_KINDS,
})

MAX_CONTINUITY_REVIEW_CONTENT_LEN: Final[int] = 4000
MAX_PERSISTED_CONTINUITY_REVIEW_RECORDS: Final[int] = 500
CONTINUITY_REVIEW_RECORD_SCHEMA_VERSION: Final[str] = "conversation_continuity_review_v1"
