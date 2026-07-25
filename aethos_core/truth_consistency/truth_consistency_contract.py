# SPDX-License-Identifier: Apache-2.0
"""FIX 316C — truth consistency contract."""

from __future__ import annotations

from typing import Final

TRUTH_CONSISTENCY_FIX: Final[str] = "FIX 316C"
TRUTH_CONSISTENCY_ROUTE_ID: Final[str] = "truth_consistency"

TRUTH_CONSISTENCY_DOMAINS: Final[tuple[str, ...]] = (
    "capability_truth_report",
    "trust_truth_report",
    "provider_truth_report",
    "identity_truth_report",
    "readiness_truth_report",
    "hallucination_detection_report",
    "truth_drift_report",
    "public_answer_validation_report",
    "truth_dashboard",
    "truth_review_registry",
)

AUTHORITY_FLAGS: Final[dict[str, bool]] = {
    "truth_authority": False,
    "automatic_truth_rewrite_enabled": False,
    "automatic_capability_promotion_enabled": False,
    "automatic_trust_mutation_enabled": False,
}

FORBIDDEN_TRUTH_ACTIONS: Final[tuple[str, ...]] = (
    "changing_answers_automatically",
    "changing_trust_states",
    "changing_capability_maturity",
    "changing_provider_readiness",
    "mutating_platform_configuration",
)

TRUTH_REVIEW_DECISION_KINDS: Final[frozenset[str]] = frozenset({
    "truth_review_decision_approve",
    "truth_review_decision_hold",
    "truth_review_decision_reject",
    "truth_review_decision_defer",
})

TRUTH_REVIEW_RECORD_KINDS: Final[frozenset[str]] = frozenset({
    "truth_note",
    *TRUTH_REVIEW_DECISION_KINDS,
})

MAX_TRUTH_REVIEW_CONTENT_LEN: Final[int] = 4000
MAX_PERSISTED_TRUTH_REVIEW_RECORDS: Final[int] = 500
TRUTH_REVIEW_RECORD_SCHEMA_VERSION: Final[str] = "truth_consistency_review_v1"

PUBLIC_ANSWER_QUESTIONS: Final[tuple[str, ...]] = (
    "what can you do?",
    "who are you?",
    "who created you?",
    "are you launch ready?",
    "which providers do you support?",
)

HALLUCINATION_MARKERS: Final[tuple[tuple[str, str], ...]] = (
    (r"\bfully\s+autonomous\b", "unsupported_capability_claim"),
    (r"\bunlimited\s+trust\b", "unsupported_trust_claim"),
    (r"\bauto(?:matically)?\s+(?:deploy|merge|launch|approve)\b", "unsupported_readiness_claim"),
    (r"\bproduction[- ]ready\s+for\s+all\s+customers\b", "unsupported_readiness_claim"),
    (r"\b(?:anthropic|openai)\s+(?:created|owns)\s+aethos\b", "unsupported_identity_claim"),
)
