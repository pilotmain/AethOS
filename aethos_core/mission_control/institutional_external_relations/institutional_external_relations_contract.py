# SPDX-License-Identifier: Apache-2.0
"""FIX 157 — institutional external relations + constitutional boundary contract."""

from __future__ import annotations

from typing import Final

INSTITUTIONAL_EXTERNAL_RELATIONS_SCHEMA_VERSION: Final[str] = (
    "mission_control_institutional_external_relations_v1"
)
INSTITUTIONAL_EXTERNAL_RELATIONS_RECORD_SCHEMA_VERSION: Final[str] = (
    "mission_control_institutional_external_relations_record_v1"
)
INSTITUTIONAL_EXTERNAL_RELATIONS_FIX: Final[str] = "FIX 157"

MUTATION_PERFORMED_FIX_157: Final[bool] = False
AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_157: Final[bool] = False
AUTONOMOUS_EXTERNAL_NEGOTIATION_ENABLED_FIX_157: Final[bool] = False
AUTONOMOUS_PROVIDER_ALIGNMENT_ENABLED_FIX_157: Final[bool] = False
SELF_DIRECTED_INSTITUTIONAL_DIPLOMACY_ENABLED_FIX_157: Final[bool] = False
SOVEREIGNTY_DELEGATION_ENABLED_FIX_157: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_157: Final[bool] = False

INSTITUTIONAL_EXTERNAL_RELATIONS_ROUTE_ID: Final[str] = "mission_control_institutional_external_relations"

INSTITUTIONAL_EXTERNAL_RELATIONS_INVARIANT: Final[str] = (
    "institutional_external_relations_is_constitutional_boundary_cognition_recommendation_only_no_autonomous_negotiation_or_sovereignty_delegation"
)

EXTERNAL_RELATIONS_RECORD_KINDS: Final[tuple[str, ...]] = (
    "provider_relationship",
    "boundary_definition",
    "trust_classification",
    "dependency_lineage",
    "interaction_policy",
    "influence_observation",
)

EXTERNAL_RELATIONS_PRINCIPLES: Final[tuple[tuple[str, str], ...]] = (
    ("boundary_not_negotiation", "Constitutional boundaries are defined and analyzed; they are never autonomously negotiated."),
    ("trust_classified_not_delegated", "External trust is classified advisory; sovereignty is never delegated to providers."),
    ("dependency_visible_not_auto_aligned", "Ecosystem dependencies are surfaced; provider alignment is never autonomous."),
    ("interoperability_advisory", "Constitutional interoperability analysis assists human boundary decisions."),
    ("influence_drift_surfaced", "External influence drift is detected and surfaced, never auto-corrected."),
    ("diplomacy_not_self_directed", "Institutional diplomacy reasoning is advisory; humans govern external relations."),
    ("provider_sovereignty_respected", "Provider sovereignty boundaries preserve institutional constitutional integrity."),
    ("cross_system_continuity_human", "Cross-system trust continuity requires human institutional stewardship."),
)

EXTERNAL_PROVIDER_CATALOG: Final[tuple[tuple[str, str, str], ...]] = (
    ("github", "software_delivery", "Governed software delivery lane — chat-governed approval only."),
    ("railway", "infrastructure_orchestration", "Railway orchestration lane — phase-governed lifecycle."),
    ("vercel", "deployment_platform", "Deployment platform boundary — observability and governance simulation only."),
    ("external_operators", "human_institution", "Human operators and governance bodies — sovereign authority."),
)

TRUST_CLASSIFICATIONS: Final[tuple[tuple[str, str], ...]] = (
    ("sovereign_internal", "Human governance and institutional constitutional stack — full trust for authority decisions."),
    ("governed_provider", "External providers under explicit chat-governed and contract-frozen boundaries."),
    ("observability_only", "External systems accessed read-only for evidence, replay, and intelligence."),
    ("untrusted_external", "External entities with no governance authority — advisory classification only."),
)

CONSTITUTIONAL_BOUNDARIES: Final[tuple[tuple[str, str], ...]] = (
    ("provider_mutation_boundary", "UI and chat never bypass provider mutation governance lanes."),
    ("mission_control_freeze_boundary", "Mission Control operator console remains read-only + governed approval only."),
    ("constitutional_cognition_boundary", "Internal constitutional cognition grants no external negotiation authority."),
    ("sovereignty_non_delegation_boundary", "Institutional sovereignty is never delegated to external providers or ecosystems."),
)

CONSTITUTIONAL_REFERENCES: Final[tuple[tuple[str, str], ...]] = (
    ("FIX 150", "Governance role architecture invariant"),
    ("FIX 156", "Institutional identity invariant"),
    ("FIX 157", "Institutional external relations invariant"),
)

EXTERNAL_RELATIONS_RECOMMENDATION_EXECUTABLE: Final[bool] = False

MAX_EXTERNAL_RELATIONS_CONTENT_LEN: Final[int] = 4000
MAX_PERSISTED_EXTERNAL_RELATIONS_RECORDS: Final[int] = 500
