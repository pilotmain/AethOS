# SPDX-License-Identifier: Apache-2.0
"""FIX 329 — enterprise operating review intelligence contract."""

from __future__ import annotations

from typing import Final

ENTERPRISE_OPERATING_REVIEW_INTELLIGENCE_SCHEMA_VERSION: Final[str] = (
    "mission_control_enterprise_operating_review_intelligence_v1"
)
ENTERPRISE_OPERATING_REVIEW_INTELLIGENCE_RECORD_SCHEMA_VERSION: Final[str] = (
    "mission_control_enterprise_operating_review_intelligence_record_v1"
)
ENTERPRISE_OPERATING_REVIEW_INTELLIGENCE_FIX: Final[str] = "FIX 329"

MUTATION_PERFORMED_FIX_329: Final[bool] = False
EXECUTION_PERFORMED_FIX_329: Final[bool] = False
OPERATING_REVIEW_AUTHORITY_FIX_329: Final[bool] = False
AUTOMATIC_STRATEGY_EXECUTION_ENABLED_FIX_329: Final[bool] = False
AUTOMATIC_PROGRAM_EXECUTION_ENABLED_FIX_329: Final[bool] = False
AUTOMATIC_ORGANIZATIONAL_CHANGES_ENABLED_FIX_329: Final[bool] = False
AUTOMATIC_DECISION_EXECUTION_ENABLED_FIX_329: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_329: Final[bool] = False
ENTERPRISE_OPERATING_REVIEW_COMPOSES_EVIDENCE_ONLY_FIX_329: Final[bool] = True

ENTERPRISE_OPERATING_REVIEW_INTELLIGENCE_ROUTE_ID: Final[str] = (
    "mission_control_enterprise_operating_review_intelligence"
)

ENTERPRISE_OPERATING_REVIEW_INTELLIGENCE_INVARIANT: Final[str] = (
    "enterprise_operating_review_intelligence_without_executive_authority"
)

ENTERPRISE_OPERATING_REVIEW_INTELLIGENCE_DOMAINS: Final[tuple[str, ...]] = (
    "executive_operating_snapshot",
    "strategic_health_review",
    "program_health_review",
    "organizational_health_review",
    "enterprise_risk_review",
    "enterprise_opportunity_review",
    "executive_action_registry",
    "executive_operating_scorecard",
    "enterprise_operating_dashboard",
    "executive_operating_review_registry",
)

STRATEGIC_HEALTH_DIMENSIONS: Final[tuple[str, ...]] = (
    "strategy_health",
    "planning_health",
    "alignment_health",
)

PROGRAM_HEALTH_DIMENSIONS: Final[tuple[str, ...]] = (
    "healthy",
    "warning",
    "at_risk",
    "blocked",
)

ORGANIZATIONAL_HEALTH_DIMENSIONS: Final[tuple[str, ...]] = (
    "governance",
    "coordination",
    "capacity",
    "decision_velocity",
)

ENTERPRISE_RISK_CATEGORIES: Final[tuple[str, ...]] = (
    "strategic",
    "program",
    "organizational",
    "operational",
)

EXECUTIVE_ACTION_TYPES: Final[tuple[str, ...]] = (
    "investigate",
    "review",
    "prioritize",
    "monitor",
)

EXECUTIVE_OPERATING_SCORECARD_DIMENSIONS: Final[tuple[str, ...]] = (
    "strategy",
    "programs",
    "organization",
    "risk",
    "execution",
)

EXECUTIVE_OPERATING_LEVELS: Final[tuple[str, ...]] = (
    "CRITICAL",
    "NEEDS_ATTENTION",
    "STABLE",
    "HEALTHY",
    "HIGH_PERFORMANCE",
)

ENTERPRISE_OPERATING_CORE_PRINCIPLE: Final[str] = (
    "enterprise_operating_review_intelligence ≠ executive_authority"
)

PRIVACY_REQUIREMENTS: Final[tuple[str, ...]] = (
    "no_cross_tenant_visibility",
    "no_automatic_decisions",
    "no_automatic_execution",
    "tenant_isolation_preserved",
)

HUMAN_OPERATING_REVIEW_DECISION_KINDS: Final[tuple[str, ...]] = (
    "operating_review_decision_approve",
    "operating_review_decision_hold",
    "operating_review_decision_reject",
    "operating_review_decision_defer",
)

OPERATING_REVIEW_RECORD_KINDS: Final[tuple[str, ...]] = (
    "operating_review_note",
    *HUMAN_OPERATING_REVIEW_DECISION_KINDS,
    "operating_review_snapshot",
)

FORBIDDEN_OPERATING_REVIEW_ACTIONS: Final[tuple[tuple[str, str], ...]] = (
    ("automatic_decision_execution", "Never executes executive decisions automatically."),
    ("automatic_strategy_execution", "Never executes strategy automatically."),
    ("automatic_program_execution", "Never executes programs automatically."),
    ("automatic_organizational_changes", "Never changes organizations automatically."),
    ("cross_tenant_operating_visibility", "Never aggregates operating signals across tenants."),
)

ENTERPRISE_OPERATING_REVIEW_INTELLIGENCE_EXECUTABLE: Final[bool] = False

MAX_OPERATING_REVIEW_CONTENT_LEN: Final[int] = 4000
MAX_PERSISTED_OPERATING_REVIEW_RECORDS: Final[int] = 500
