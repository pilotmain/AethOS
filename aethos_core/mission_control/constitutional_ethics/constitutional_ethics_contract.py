# SPDX-License-Identifier: Apache-2.0
"""FIX 159 — constitutional ethics + institutional moral reasoning contract."""

from __future__ import annotations

from typing import Final

CONSTITUTIONAL_ETHICS_SCHEMA_VERSION: Final[str] = "mission_control_constitutional_ethics_v1"
CONSTITUTIONAL_ETHICS_RECORD_SCHEMA_VERSION: Final[str] = "mission_control_constitutional_ethics_record_v1"
CONSTITUTIONAL_ETHICS_FIX: Final[str] = "FIX 159"

MUTATION_PERFORMED_FIX_159: Final[bool] = False
AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_159: Final[bool] = False
AUTONOMOUS_MORAL_AUTHORITY_ENABLED_FIX_159: Final[bool] = False
SELF_AUTHORED_ETHICS_ENABLED_FIX_159: Final[bool] = False
CONSTITUTIONAL_OVERRIDE_AUTHORITY_ENABLED_FIX_159: Final[bool] = False
VALUE_ENFORCEMENT_AUTHORITY_ENABLED_FIX_159: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_159: Final[bool] = False

CONSTITUTIONAL_ETHICS_ROUTE_ID: Final[str] = "mission_control_constitutional_ethics"

CONSTITUTIONAL_ETHICS_INVARIANT: Final[str] = (
    "constitutional_ethics_is_moral_reasoning_cognition_recommendation_only_no_autonomous_moral_authority_or_value_enforcement"
)

ETHICS_RECORD_KINDS: Final[tuple[str, ...]] = (
    "ethics_record",
    "value_conflict_note",
    "moral_tradeoff",
    "ethical_tension_observation",
    "value_preservation_note",
    "moral_precedent",
)

ETHICS_PRINCIPLES: Final[tuple[tuple[str, str], ...]] = (
    ("values_reasoned_not_enforced", "Institutional values are reasoned about under conflict; never autonomously enforced."),
    ("ethics_advisory_not_sovereign", "Ethical cognition assists human moral stewardship; never grants moral sovereignty."),
    ("no_self_authored_ethics", "Ethics are never self-authored by the system — humans govern constitutional values."),
    ("tradeoffs_surfaced_not_resolved", "Moral tradeoffs are analyzed and surfaced; resolution remains human-governed."),
    ("ambiguity_surfaced_not_collapsed", "Ethical ambiguity is surfaced for deliberation; never collapsed autonomously."),
    ("precedent_assists_not_rules", "Moral precedent analysis assists reasoning; never becomes autonomous enforcement."),
    ("value_drift_detected_not_corrected", "Constitutional value drift is detected; never auto-corrected or redirected."),
    ("coherence_scored_not_imposed", "Ethical coherence scoring is advisory; never imposed as authority."),
)

CONSTITUTIONAL_VALUE_CATALOG: Final[tuple[tuple[str, str], ...]] = (
    ("human_sovereignty", "Human operators retain sovereign authority over all governance and ethical decisions."),
    ("chat_governed_mutation", "All provider mutations require chat-governed approval — no bypass authority."),
    ("constitutional_boundedness", "Constitutional cognition layers grant reasoning without authority."),
    ("institutional_continuity", "Institutional continuity preserved through human stewardship, not autonomous self-preservation."),
    ("transparency_and_replay", "Operational truth, evidence, and replay preserve institutional accountability."),
)

VALUE_CONFLICT_PATTERNS: Final[tuple[tuple[str, str, str], ...]] = (
    ("mission_urgency_vs_governance_safety", "moderate", "Mission urgency pressures governance safety boundaries."),
    ("provider_efficiency_vs_constitutional_integrity", "elevated", "External provider efficiency conflicts with constitutional integrity."),
    ("operational_velocity_vs_deliberation_depth", "moderate", "Operational velocity conflicts with governance deliberation depth."),
    ("existential_preservation_vs_sovereignty_non_delegation", "elevated", "Continuity preservation tension with sovereignty non-delegation."),
)

MORAL_PRECEDENT_CATALOG: Final[tuple[tuple[str, str], ...]] = (
    ("approval_before_mutation", "Provider mutations require explicit human approval — precedent of chat-governed authority."),
    ("read_only_mission_control", "Mission Control remains observability-first — precedent of non-autonomous governance."),
    ("cognition_without_authority", "Each constitutional layer reasons without authority — precedent of bounded cognition."),
)

CONSTITUTIONAL_REFERENCES: Final[tuple[tuple[str, str], ...]] = (
    ("FIX 156", "Institutional identity invariant"),
    ("FIX 158", "Institutional existential risk invariant"),
    ("FIX 159", "Constitutional ethics invariant"),
)

ETHICS_RECOMMENDATION_EXECUTABLE: Final[bool] = False

MAX_ETHICS_CONTENT_LEN: Final[int] = 4000
MAX_PERSISTED_ETHICS_RECORDS: Final[int] = 500
