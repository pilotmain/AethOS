# SPDX-License-Identifier: Apache-2.0
"""FIX 320 — growth & adoption intelligence contract."""

from __future__ import annotations

from typing import Final

GROWTH_ADOPTION_INTELLIGENCE_SCHEMA_VERSION: Final[str] = "mission_control_growth_adoption_intelligence_v1"
GROWTH_ADOPTION_INTELLIGENCE_RECORD_SCHEMA_VERSION: Final[str] = (
    "mission_control_growth_adoption_intelligence_record_v1"
)
GROWTH_ADOPTION_INTELLIGENCE_FIX: Final[str] = "FIX 320"

MUTATION_PERFORMED_FIX_320: Final[bool] = False
EXECUTION_PERFORMED_FIX_320: Final[bool] = False
GROWTH_AUTHORITY_FIX_320: Final[bool] = False
AUTOMATIC_CUSTOMER_OUTREACH_ENABLED_FIX_320: Final[bool] = False
AUTOMATIC_PLAN_UPGRADE_ENABLED_FIX_320: Final[bool] = False
AUTOMATIC_CUSTOMER_TARGETING_ENABLED_FIX_320: Final[bool] = False
AUTOMATIC_GROWTH_EXECUTION_ENABLED_FIX_320: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_320: Final[bool] = False
GROWTH_ADOPTION_COMPOSES_EVIDENCE_ONLY_FIX_320: Final[bool] = True

GROWTH_ADOPTION_INTELLIGENCE_ROUTE_ID: Final[str] = "mission_control_growth_adoption_intelligence"

GROWTH_ADOPTION_INTELLIGENCE_INVARIANT: Final[str] = (
    "growth_adoption_intelligence_without_automatic_growth_execution"
)

GROWTH_ADOPTION_INTELLIGENCE_DOMAINS: Final[tuple[str, ...]] = (
    "adoption_registry",
    "adoption_analytics_report",
    "retention_intelligence_report",
    "expansion_intelligence_report",
    "success_pattern_report",
    "churn_risk_report",
    "growth_opportunity_registry",
    "growth_priority_matrix",
    "growth_adoption_dashboard",
    "growth_review_registry",
)

GROWTH_OPPORTUNITY_TYPES: Final[tuple[str, ...]] = (
    "adoption",
    "retention",
    "expansion",
)

GROWTH_CORE_PRINCIPLE: Final[str] = "growth_intelligence ≠ growth_execution"

PRIVACY_REQUIREMENTS: Final[tuple[str, ...]] = (
    "no_cross_tenant_growth_analysis",
    "no_customer_profiling",
    "no_customer_targeting",
    "no_automatic_campaigns",
    "no_automatic_outreach",
    "tenant_isolation_preserved",
)

HUMAN_GROWTH_REVIEW_DECISION_KINDS: Final[tuple[str, ...]] = (
    "growth_review_decision_approve",
    "growth_review_decision_hold",
    "growth_review_decision_reject",
    "growth_review_decision_defer",
)

GROWTH_REVIEW_RECORD_KINDS: Final[tuple[str, ...]] = (
    "growth_note",
    *HUMAN_GROWTH_REVIEW_DECISION_KINDS,
    "growth_snapshot",
)

FORBIDDEN_GROWTH_ACTIONS: Final[tuple[tuple[str, str], ...]] = (
    ("automatic_customer_outreach", "Never contacts customers automatically."),
    ("automatic_plan_upgrade", "Never upgrades plans automatically."),
    ("automatic_customer_targeting", "Never targets customers automatically."),
    ("automatic_growth_execution", "Never executes growth campaigns automatically."),
    ("cross_tenant_growth_analysis", "Never aggregates growth signals across tenants."),
)

GROWTH_ADOPTION_INTELLIGENCE_EXECUTABLE: Final[bool] = False

MAX_GROWTH_REVIEW_CONTENT_LEN: Final[int] = 4000
MAX_PERSISTED_GROWTH_REVIEW_RECORDS: Final[int] = 500

IMPACT_LEVELS: Final[tuple[str, ...]] = ("high", "medium", "low")
EFFORT_LEVELS: Final[tuple[str, ...]] = ("low", "medium", "high")
CONFIDENCE_LEVELS: Final[tuple[str, ...]] = ("high", "medium", "low")
