# SPDX-License-Identifier: Apache-2.0
"""FIX 327 — enterprise program intelligence contract."""

from __future__ import annotations

from typing import Final

ENTERPRISE_PROGRAM_INTELLIGENCE_SCHEMA_VERSION: Final[str] = "mission_control_enterprise_program_intelligence_v1"
ENTERPRISE_PROGRAM_INTELLIGENCE_RECORD_SCHEMA_VERSION: Final[str] = (
    "mission_control_enterprise_program_intelligence_record_v1"
)
ENTERPRISE_PROGRAM_INTELLIGENCE_FIX: Final[str] = "FIX 327"

MUTATION_PERFORMED_FIX_327: Final[bool] = False
EXECUTION_PERFORMED_FIX_327: Final[bool] = False
PROGRAM_AUTHORITY_FIX_327: Final[bool] = False
AUTOMATIC_PROJECT_CREATION_ENABLED_FIX_327: Final[bool] = False
AUTOMATIC_PROGRAM_EXECUTION_ENABLED_FIX_327: Final[bool] = False
AUTOMATIC_RESOURCE_ASSIGNMENT_ENABLED_FIX_327: Final[bool] = False
AUTOMATIC_DEPENDENCY_RESOLUTION_ENABLED_FIX_327: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_327: Final[bool] = False
ENTERPRISE_PROGRAM_COMPOSES_EVIDENCE_ONLY_FIX_327: Final[bool] = True

ENTERPRISE_PROGRAM_INTELLIGENCE_ROUTE_ID: Final[str] = "mission_control_enterprise_program_intelligence"

ENTERPRISE_PROGRAM_INTELLIGENCE_INVARIANT: Final[str] = (
    "enterprise_program_intelligence_without_program_execution_authority"
)

ENTERPRISE_PROGRAM_INTELLIGENCE_DOMAINS: Final[tuple[str, ...]] = (
    "program_registry",
    "program_dependency_report",
    "program_health_report",
    "program_progress_report",
    "program_risk_report",
    "program_alignment_report",
    "program_opportunity_registry",
    "program_priority_matrix",
    "enterprise_program_dashboard",
    "program_review_registry",
)

PROGRAM_ENTITY_TYPES: Final[tuple[str, ...]] = (
    "strategic_program",
    "initiative",
    "project",
    "workstream",
)

PROGRAM_HEALTH_STATUSES: Final[tuple[str, ...]] = (
    "healthy",
    "warning",
    "at_risk",
    "blocked",
)

PROGRAM_OPPORTUNITY_TYPES: Final[tuple[str, ...]] = (
    "acceleration",
    "efficiency",
    "dependency_reduction",
)

ENTERPRISE_PROGRAM_CORE_PRINCIPLE: Final[str] = (
    "enterprise_program_intelligence ≠ program_execution_authority"
)

PRIVACY_REQUIREMENTS: Final[tuple[str, ...]] = (
    "no_cross_tenant_program_visibility",
    "no_automatic_execution",
    "no_automatic_resource_movement",
    "tenant_isolation_preserved",
)

HUMAN_PROGRAM_REVIEW_DECISION_KINDS: Final[tuple[str, ...]] = (
    "program_review_decision_approve",
    "program_review_decision_hold",
    "program_review_decision_reject",
    "program_review_decision_defer",
)

PROGRAM_REVIEW_RECORD_KINDS: Final[tuple[str, ...]] = (
    "program_note",
    *HUMAN_PROGRAM_REVIEW_DECISION_KINDS,
    "program_snapshot",
)

FORBIDDEN_PROGRAM_ACTIONS: Final[tuple[tuple[str, str], ...]] = (
    ("automatic_program_execution", "Never executes programs automatically."),
    ("automatic_project_creation", "Never creates projects automatically."),
    ("automatic_resource_assignment", "Never assigns resources automatically."),
    ("automatic_dependency_resolution", "Never resolves dependencies automatically."),
    ("cross_tenant_program_visibility", "Never aggregates program signals across tenants."),
)

ENTERPRISE_PROGRAM_INTELLIGENCE_EXECUTABLE: Final[bool] = False

MAX_PROGRAM_REVIEW_CONTENT_LEN: Final[int] = 4000
MAX_PERSISTED_PROGRAM_REVIEW_RECORDS: Final[int] = 500

EXECUTION_CONFIDENCE_LEVELS: Final[tuple[str, ...]] = ("low", "medium", "high")
