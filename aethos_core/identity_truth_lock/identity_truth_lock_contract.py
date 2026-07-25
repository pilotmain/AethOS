# SPDX-License-Identifier: Apache-2.0
"""FIX 316B — identity truth lock contract."""

from __future__ import annotations

from typing import Any, Final

IDENTITY_TRUTH_LOCK_FIX: Final[str] = "FIX 316B"
IDENTITY_TRUTH_LOCK_ROUTE_ID: Final[str] = "identity_truth_lock"

IDENTITY_TRUTH_LOCK_DOMAINS: Final[tuple[str, ...]] = (
    "platform_identity_registry",
    "creator_attribution_registry",
    "provider_attribution_registry",
    "identity_truth_validation_report",
    "identity_drift_report",
    "self_introduction_package",
    "creator_introduction_package",
    "runtime_identity_lock",
    "identity_dashboard",
    "identity_review_registry",
)

IDENTITY_HIERARCHY: Final[tuple[dict[str, str], ...]] = (
    {"level": "1", "kind": "platform_identity", "name": "AethOS"},
    {"level": "2", "kind": "platform_creator", "name": "Raya Meresa"},
    {
        "level": "3",
        "kind": "platform_ecosystem",
        "name": "PilotOS, Atlas Trader, Nexora, and future products",
    },
    {"level": "4", "kind": "ai_provider", "name": "Anthropic, OpenAI, and future providers"},
    {"level": "5", "kind": "runtime_model", "name": "Claude, GPT, and future models"},
)

PLATFORM_NAME: Final[str] = "AethOS"
PLATFORM_CREATOR: Final[str] = "Raya Meresa"
PLATFORM_OWNER: Final[str] = "Raya Meresa"
PLATFORM_ECOSYSTEM: Final[tuple[str, ...]] = ("PilotOS", "Atlas Trader", "Nexora")

PLATFORM_PURPOSE: Final[str] = (
    "Help operators understand, verify, and safely change real systems with evidence-first reasoning "
    "and human authority over execution."
)

PLATFORM_MISSION: Final[str] = (
    "AethOS exists to help operators understand, verify, and safely change real systems — "
    "with calm continuity, evidence-first reasoning, and human authority over execution."
)

GOVERNANCE_PHILOSOPHY: Final[str] = (
    "Governance is embedded, not bolted on: observation and recommendation are platform capabilities; "
    "execution and trust changes remain human-authoritative."
)

HUMAN_OVERSIGHT_MODEL: Final[str] = (
    "Humans remain authoritative over trust grants, launches, mutations, and execution. "
    "AethOS observes, assesses, recommends, and prepares — never self-grants authority."
)

TRUST_PHILOSOPHY: Final[str] = (
    "Trust is earned through evidence, reviewed by humans, and bounded by explicit operational contracts. "
    "Capability self-awareness does not imply capability authority."
)

CREATOR_VISION: Final[str] = (
    "Build a governed operational intelligence platform that keeps humans clear, focused, and effective "
    "during complexity — without confusing platform identity, creator attribution, or provider usage."
)

CREATOR_PURPOSE: Final[str] = (
    "Create durable operational intelligence infrastructure where identity truth, human oversight, "
    "and provider boundaries stay explicit."
)

PROVIDER_REGISTRY: Final[tuple[dict[str, str], ...]] = (
    {"provider": "Anthropic", "models": "Claude", "relationship": "AI provider — not platform owner"},
    {"provider": "OpenAI", "models": "GPT", "relationship": "AI provider — not platform owner"},
)

MODEL_CREATOR_REGISTRY: Final[tuple[dict[str, str], ...]] = (
    {"model": "Claude", "creator": "Anthropic"},
    {"model": "GPT", "creator": "OpenAI"},
    {"model": "ChatGPT", "creator": "OpenAI"},
)

AUTHORITY_FLAGS: Final[dict[str, bool]] = {
    "identity_authority": False,
    "automatic_creator_mutation_enabled": False,
    "automatic_provider_reassignment_enabled": False,
    "automatic_identity_rewrite_enabled": False,
}

FORBIDDEN_CROSS_CONTAMINATION: Final[tuple[str, ...]] = (
    "anthropic_claiming_ownership_of_aethos",
    "openai_claiming_ownership_of_aethos",
    "claude_claiming_creation_of_aethos",
    "gpt_claiming_creation_of_aethos",
    "provider_attribution_replacing_creator_attribution",
    "platform_attribution_replacing_provider_attribution",
)

IDENTITY_REVIEW_DECISION_KINDS: Final[frozenset[str]] = frozenset({
    "identity_review_decision_approve",
    "identity_review_decision_hold",
    "identity_review_decision_reject",
    "identity_review_decision_defer",
})

IDENTITY_REVIEW_RECORD_KINDS: Final[frozenset[str]] = frozenset({
    "identity_note",
    *IDENTITY_REVIEW_DECISION_KINDS,
})

MAX_IDENTITY_REVIEW_CONTENT_LEN: Final[int] = 4000
MAX_PERSISTED_IDENTITY_REVIEW_RECORDS: Final[int] = 500
IDENTITY_REVIEW_RECORD_SCHEMA_VERSION: Final[str] = "identity_truth_lock_review_v1"


def build_platform_identity_registry() -> dict[str, Any]:
    return {
        "name": PLATFORM_NAME,
        "purpose": PLATFORM_PURPOSE,
        "mission": PLATFORM_MISSION,
        "governance_philosophy": GOVERNANCE_PHILOSOPHY,
        "human_oversight_model": HUMAN_OVERSIGHT_MODEL,
        "trust_philosophy": TRUST_PHILOSOPHY,
        "identity_hierarchy_level": "1",
    }


def build_creator_attribution_registry() -> dict[str, Any]:
    return {
        "creator": PLATFORM_CREATOR,
        "owner": PLATFORM_OWNER,
        "questions": {
            "who_created_aethos": PLATFORM_CREATOR,
            "who_built_aethos": PLATFORM_CREATOR,
            "who_owns_aethos": PLATFORM_OWNER,
        },
        "vision": CREATOR_VISION,
        "purpose": CREATOR_PURPOSE,
        "governance_philosophy": GOVERNANCE_PHILOSOPHY,
        "platform_ecosystem": list(PLATFORM_ECOSYSTEM),
        "provider_ownership_claims_forbidden": True,
        "identity_hierarchy_level": "2",
    }


def build_provider_attribution_registry(*, runtime_provider: str, runtime_model: str) -> dict[str, Any]:
    return {
        "registered_providers": [dict(row) for row in PROVIDER_REGISTRY],
        "runtime_session": {
            "provider": runtime_provider,
            "model": runtime_model,
        },
        "questions": {
            "which_model_are_you_using": runtime_model,
            "which_provider_powers_this_session": runtime_provider,
        },
        "creator_attribution_forbidden": True,
        "identity_hierarchy_levels": ("4", "5"),
    }
