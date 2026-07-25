# SPDX-License-Identifier: Apache-2.0
"""FIX 316A — runtime truth alignment contract."""

from __future__ import annotations

from typing import Final

RUNTIME_TRUTH_ALIGNMENT_FIX: Final[str] = "FIX 316A"
RUNTIME_TRUTH_ALIGNMENT_ROUTE_ID: Final[str] = "runtime_truth_alignment"

RUNTIME_CLASSIFICATION_DOMAINS: Final[tuple[str, ...]] = (
    "platform_identity_response",
    "capability_response",
    "human_support_response",
    "general_assistant_response",
    "operational_action",
)

PLATFORM_IDENTITY_INTENTS: Final[frozenset[str]] = frozenset({
    "platform_identity_response",
    "creator_attribution_response",
})

NON_OPERATIONAL_INTENTS: Final[frozenset[str]] = frozenset({
    "platform_identity_response",
    "creator_attribution_response",
    "capability_response",
    "human_support_response",
    "general_assistant_response",
    "greeting",
    "identity_intro",
    "capability_question",
    "generative_answer",
})

CREATOR_ATTRIBUTION: Final[str] = (
    "**Raya Meresa** created and built **AethOS** — a governed operational intelligence platform "
    "built to help teams understand, verify, and safely change real systems."
)

GOVERNANCE_PHILOSOPHY: Final[str] = (
    "Governance is embedded, not bolted on: observation and recommendation are platform capabilities; "
    "execution and trust changes remain human-authoritative."
)
