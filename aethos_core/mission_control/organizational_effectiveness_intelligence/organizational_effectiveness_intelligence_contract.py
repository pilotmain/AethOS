# SPDX-License-Identifier: Apache-2.0
"""FIX 328 — organizational effectiveness intelligence contract."""

from __future__ import annotations

from typing import Final

ORGANIZATIONAL_EFFECTIVENESS_INTELLIGENCE_SCHEMA_VERSION: Final[str] = (
    "mission_control_organizational_effectiveness_intelligence_v1"
)
ORGANIZATIONAL_EFFECTIVENESS_INTELLIGENCE_RECORD_SCHEMA_VERSION: Final[str] = (
    "mission_control_organizational_effectiveness_intelligence_record_v1"
)
ORGANIZATIONAL_EFFECTIVENESS_INTELLIGENCE_FIX: Final[str] = "FIX 328"

MUTATION_PERFORMED_FIX_328: Final[bool] = False
EXECUTION_PERFORMED_FIX_328: Final[bool] = False
ORGANIZATIONAL_AUTHORITY_FIX_328: Final[bool] = False
AUTOMATIC_ROLE_CHANGES_ENABLED_FIX_328: Final[bool] = False
AUTOMATIC_GOVERNANCE_CHANGES_ENABLED_FIX_328: Final[bool] = False
AUTOMATIC_RESOURCE_REALLOCATION_ENABLED_FIX_328: Final[bool] = False
AUTOMATIC_ORGANIZATIONAL_CHANGES_ENABLED_FIX_328: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_328: Final[bool] = False
ORGANIZATIONAL_EFFECTIVENESS_COMPOSES_EVIDENCE_ONLY_FIX_328: Final[bool] = True

ORGANIZATIONAL_EFFECTIVENESS_INTELLIGENCE_ROUTE_ID: Final[str] = (
    "mission_control_organizational_effectiveness_intelligence"
)

ORGANIZATIONAL_EFFECTIVENESS_INTELLIGENCE_INVARIANT: Final[str] = (
    "organizational_effectiveness_intelligence_without_organizational_authority"
)

ORGANIZATIONAL_EFFECTIVENESS_INTELLIGENCE_DOMAINS: Final[tuple[str, ...]] = (
    "organizational_structure_registry",
    "governance_friction_report",
    "coordination_intelligence_report",
    "organizational_capacity_report",
    "decision_velocity_report",
    "organizational_risk_report",
    "organizational_opportunity_registry",
    "organizational_effectiveness_scorecard",
    "organizational_effectiveness_dashboard",
    "organizational_review_registry",
)

ORGANIZATIONAL_EFFECTIVENESS_SCORECARD_DIMENSIONS: Final[tuple[str, ...]] = (
    "governance",
    "coordination",
    "capacity",
    "decision_velocity",
    "execution_effectiveness",
)

ORGANIZATIONAL_EFFECTIVENESS_LEVELS: Final[tuple[str, ...]] = (
    "CRITICAL",
    "NEEDS_IMPROVEMENT",
    "STABLE",
    "EFFECTIVE",
    "HIGH_PERFORMANCE",
)

ORGANIZATIONAL_OPPORTUNITY_TYPES: Final[tuple[str, ...]] = (
    "efficiency",
    "coordination",
    "governance",
)

ORGANIZATIONAL_RISK_CATEGORIES: Final[tuple[str, ...]] = (
    "execution_risk",
    "dependency_risk",
    "governance_risk",
    "operational_risk",
)

ORGANIZATIONAL_CORE_PRINCIPLE: Final[str] = (
    "organizational_effectiveness_intelligence ≠ organizational_authority"
)

PRIVACY_REQUIREMENTS: Final[tuple[str, ...]] = (
    "no_cross_tenant_visibility",
    "no_personnel_evaluation",
    "no_automatic_organizational_restructuring",
    "tenant_isolation_preserved",
)

HUMAN_ORGANIZATIONAL_REVIEW_DECISION_KINDS: Final[tuple[str, ...]] = (
    "organization_review_decision_approve",
    "organization_review_decision_hold",
    "organization_review_decision_reject",
    "organization_review_decision_defer",
)

ORGANIZATIONAL_REVIEW_RECORD_KINDS: Final[tuple[str, ...]] = (
    "organization_note",
    *HUMAN_ORGANIZATIONAL_REVIEW_DECISION_KINDS,
    "organization_snapshot",
)

FORBIDDEN_ORGANIZATIONAL_ACTIONS: Final[tuple[tuple[str, str], ...]] = (
    ("automatic_role_changes", "Never changes roles automatically."),
    ("automatic_governance_changes", "Never changes governance automatically."),
    ("automatic_resource_reallocation", "Never reallocates resources automatically."),
    ("automatic_organizational_changes", "Never restructures organizations automatically."),
    ("cross_tenant_organizational_visibility", "Never aggregates organizational signals across tenants."),
)

ORGANIZATIONAL_EFFECTIVENESS_INTELLIGENCE_EXECUTABLE: Final[bool] = False

MAX_ORGANIZATIONAL_REVIEW_CONTENT_LEN: Final[int] = 4000
MAX_PERSISTED_ORGANIZATIONAL_REVIEW_RECORDS: Final[int] = 500
