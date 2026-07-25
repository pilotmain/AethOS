# SPDX-License-Identifier: Apache-2.0
"""FIX 160 — constitutional audit + public accountability contract."""

from __future__ import annotations

from typing import Final

CONSTITUTIONAL_AUDIT_SCHEMA_VERSION: Final[str] = "mission_control_constitutional_audit_v1"
CONSTITUTIONAL_AUDIT_RECORD_SCHEMA_VERSION: Final[str] = "mission_control_constitutional_audit_record_v1"
CONSTITUTIONAL_AUDIT_FIX: Final[str] = "FIX 160"

MUTATION_PERFORMED_FIX_160: Final[bool] = False
AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_160: Final[bool] = False
AUTONOMOUS_DISCLOSURE_ENABLED_FIX_160: Final[bool] = False
PUBLIC_COMMUNICATION_AUTHORITY_ENABLED_FIX_160: Final[bool] = False
GOVERNANCE_ENFORCEMENT_ENABLED_FIX_160: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_160: Final[bool] = False

CONSTITUTIONAL_AUDIT_ROUTE_ID: Final[str] = "mission_control_constitutional_audit"

CONSTITUTIONAL_AUDIT_INVARIANT: Final[str] = (
    "constitutional_audit_is_accountability_cognition_recommendation_only_no_autonomous_disclosure_or_public_communication_authority"
)

AUDIT_RECORD_KINDS: Final[tuple[str, ...]] = (
    "audit_report",
    "reasoning_summary",
    "accountability_record",
    "recommendation_explanation",
    "disclosure_boundary_note",
)

ACCOUNTABILITY_PRINCIPLES: Final[tuple[tuple[str, str], ...]] = (
    ("explain_not_disclose", "Constitutional reasoning is explained and auditable; disclosure remains human-governed."),
    ("traceable_not_authoritative", "Traceable reasoning summaries assist accountability; never grant public communication authority."),
    ("audit_assists_not_enforces", "Audit reports assist human governance; never enforce policy autonomously."),
    ("linkage_visible_not_mutated", "Doctrine/ethics/existential linkage is surfaced; never autonomously mutated."),
    ("public_safe_not_public_authority", "Public-safe summaries assist disclosure decisions; humans decide what to publish."),
    ("internal_external_bounded", "Internal vs external disclosure boundaries preserve institutional sovereignty."),
    ("transparency_scored_not_imposed", "Transparency scoring is advisory; never imposed as disclosure mandate."),
    ("integrity_checked_not_overridden", "Audit trail integrity is verified; never overridden autonomously."),
)

CONSTITUTIONAL_LAYER_LINKAGE: Final[tuple[tuple[str, str, str], ...]] = (
    ("doctrine", "FIX 151", "Governance doctrine and policy charter — amendment proposals only."),
    ("interpretation", "FIX 152", "Policy interpretation and precedent application — assistance only."),
    ("coherence", "FIX 153", "Governance coherence and constitutional integrity — recommendation-only."),
    ("resilience", "FIX 154", "Governance resilience and stress simulation — simulation-only."),
    ("evolution", "FIX 155", "Governance evolution and institutional continuity — recommendation-only."),
    ("identity", "FIX 156", "Institutional identity and constitutional intent — identity cognition only."),
    ("external_relations", "FIX 157", "External relations and constitutional boundaries — no negotiation authority."),
    ("existential_risk", "FIX 158", "Existential risk and continuity preservation — no self-preservation authority."),
    ("ethics", "FIX 159", "Constitutional ethics and moral reasoning — no moral sovereignty."),
    ("audit", "FIX 160", "Constitutional audit and public accountability — no disclosure authority."),
)

DISCLOSURE_BOUNDARIES: Final[tuple[tuple[str, str], ...]] = (
    ("internal_full_audit", "Full constitutional audit reports for internal human governance review."),
    ("operator_governance_evidence", "Human-readable governance evidence bundles for operator accountability."),
    ("public_safe_summary", "Public-safe accountability summaries — redacted, human-approved disclosure only."),
    ("no_autonomous_external_disclosure", "External disclosure never autonomous — humans govern all public communication."),
)

CONSTITUTIONAL_REFERENCES: Final[tuple[tuple[str, str], ...]] = (
    ("FIX 159", "Constitutional ethics invariant"),
    ("FIX 160", "Constitutional audit invariant"),
)

AUDIT_RECOMMENDATION_EXECUTABLE: Final[bool] = False

MAX_AUDIT_CONTENT_LEN: Final[int] = 4000
MAX_PERSISTED_AUDIT_RECORDS: Final[int] = 500
