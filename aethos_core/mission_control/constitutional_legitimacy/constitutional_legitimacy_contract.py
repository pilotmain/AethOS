# SPDX-License-Identifier: Apache-2.0
"""FIX 161 — constitutional legitimacy + institutional trust contract."""

from __future__ import annotations

from typing import Final

CONSTITUTIONAL_LEGITIMACY_SCHEMA_VERSION: Final[str] = "mission_control_constitutional_legitimacy_v1"
CONSTITUTIONAL_LEGITIMACY_RECORD_SCHEMA_VERSION: Final[str] = "mission_control_constitutional_legitimacy_record_v1"
CONSTITUTIONAL_LEGITIMACY_FIX: Final[str] = "FIX 161"

MUTATION_PERFORMED_FIX_161: Final[bool] = False
AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_161: Final[bool] = False
AUTONOMOUS_LEGITIMACY_ENFORCEMENT_ENABLED_FIX_161: Final[bool] = False
PUBLIC_TRUST_MANIPULATION_ENABLED_FIX_161: Final[bool] = False
CONSTITUTIONAL_AUTHORITY_EXPANSION_ENABLED_FIX_161: Final[bool] = False
SOVEREIGNTY_DELEGATION_ENABLED_FIX_161: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_161: Final[bool] = False

CONSTITUTIONAL_LEGITIMACY_ROUTE_ID: Final[str] = "mission_control_constitutional_legitimacy"

CONSTITUTIONAL_LEGITIMACY_INVARIANT: Final[str] = (
    "constitutional_legitimacy_is_trust_cognition_recommendation_only_no_autonomous_legitimacy_enforcement_or_public_trust_manipulation"
)

LEGITIMACY_RECORD_KINDS: Final[tuple[str, ...]] = (
    "trust_continuity_note",
    "legitimacy_indicator",
    "stakeholder_confidence_note",
    "credibility_drift_signal",
    "legitimacy_tracking_record",
)

LEGITIMACY_PRINCIPLES: Final[tuple[tuple[str, str], ...]] = (
    ("trust_analyzed_not_manipulated", "Institutional trust is analyzed; public trust is never autonomously manipulated."),
    ("legitimacy_surfaced_not_enforced", "Governance legitimacy indicators assist human stewardship; never auto-enforced."),
    ("confidence_reasoned_not_authored", "Stakeholder confidence is reasoned about; never autonomously authored or manufactured."),
    ("credibility_drift_detected_not_reconstructed", "Credibility drift is detected; reconstruction remains human-governed."),
    ("fragmentation_surfaced_not_healed", "Trust fragmentation is surfaced; healing remains human institutional work."),
    ("participation_health_advisory", "Constitutional participation health is advisory; never grants authority expansion."),
    ("transparency_trust_linked_not_mandated", "Transparency-trust linkage assists credibility; never mandates disclosure."),
    ("sovereignty_never_delegated_for_legitimacy", "Legitimacy cognition grants no sovereignty delegation or authority expansion."),
)

GOVERNANCE_LEGITIMACY_INDICATORS: Final[tuple[tuple[str, str, str], ...]] = (
    ("chat_governed_approval_continuity", "strong", "Provider mutations remain chat-governed — legitimacy through bounded authority."),
    ("mission_control_read_only_integrity", "strong", "Mission Control observability preserves institutional trust boundaries."),
    ("constitutional_stack_completeness", "moderate", "Full constitutional cognition stack supports long-horizon legitimacy."),
    ("audit_trail_accountability", "strong", "Audit trail integrity supports governance credibility reconstruction."),
    ("no_autonomous_authority_creep", "critical", "Absence of autonomous authority expansion preserves institutional legitimacy."),
)

STAKEHOLDER_CONFIDENCE_DIMENSIONS: Final[tuple[tuple[str, str], ...]] = (
    ("operator_confidence", "Operator trust in chat-governed governance and Mission Control observability."),
    ("governance_participant_confidence", "Confidence of constitutional participants in bounded cognition layers."),
    ("institutional_stakeholder_confidence", "Long-horizon stakeholder trust in institutional continuity and ethics."),
)

CONSTITUTIONAL_REFERENCES: Final[tuple[tuple[str, str], ...]] = (
    ("FIX 160", "Constitutional audit invariant"),
    ("FIX 161", "Constitutional legitimacy invariant"),
)

LEGITIMACY_RECOMMENDATION_EXECUTABLE: Final[bool] = False

MAX_LEGITIMACY_CONTENT_LEN: Final[int] = 4000
MAX_PERSISTED_LEGITIMACY_RECORDS: Final[int] = 500
