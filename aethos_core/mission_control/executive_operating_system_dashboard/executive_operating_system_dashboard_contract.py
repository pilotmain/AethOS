# SPDX-License-Identifier: Apache-2.0
"""FIX 330 — executive operating system dashboard contract."""

from __future__ import annotations

from typing import Final

EXECUTIVE_OPERATING_SYSTEM_DASHBOARD_SCHEMA_VERSION: Final[str] = (
    "mission_control_executive_operating_system_dashboard_v1"
)
EXECUTIVE_OPERATING_SYSTEM_DASHBOARD_RECORD_SCHEMA_VERSION: Final[str] = (
    "mission_control_executive_operating_system_dashboard_record_v1"
)
EXECUTIVE_OPERATING_SYSTEM_DASHBOARD_FIX: Final[str] = "FIX 330"

MUTATION_PERFORMED_FIX_330: Final[bool] = False
EXECUTION_PERFORMED_FIX_330: Final[bool] = False
EXECUTIVE_DASHBOARD_AUTHORITY_FIX_330: Final[bool] = False
AUTOMATIC_EXECUTION_ENABLED_FIX_330: Final[bool] = False
AUTOMATIC_DECISION_ENABLED_FIX_330: Final[bool] = False
AUTOMATIC_STRATEGY_EXECUTION_ENABLED_FIX_330: Final[bool] = False
AUTOMATIC_OPERATIONAL_EXECUTION_ENABLED_FIX_330: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_330: Final[bool] = False
EXECUTIVE_DASHBOARD_COMPOSES_EVIDENCE_ONLY_FIX_330: Final[bool] = True

EXECUTIVE_OPERATING_SYSTEM_DASHBOARD_ROUTE_ID: Final[str] = (
    "mission_control_executive_operating_system_dashboard"
)

EXECUTIVE_OPERATING_SYSTEM_DASHBOARD_INVARIANT: Final[str] = (
    "executive_operating_system_dashboard_without_executive_authority"
)

EXECUTIVE_OPERATING_SYSTEM_DASHBOARD_DOMAINS: Final[tuple[str, ...]] = (
    "executive_summary_panel",
    "strategy_panel",
    "program_panel",
    "organization_panel",
    "customer_panel",
    "operations_panel",
    "commercial_panel",
    "portfolio_panel",
    "executive_operating_system_dashboard",
    "executive_dashboard_review_registry",
)

EXECUTIVE_DASHBOARD_CORE_PRINCIPLE: Final[str] = (
    "executive_dashboard_visibility ≠ executive_authority"
)

PRIVACY_REQUIREMENTS: Final[tuple[str, ...]] = (
    "no_cross_tenant_visibility",
    "no_automatic_execution",
    "no_authority_escalation",
    "tenant_isolation_preserved",
)

HUMAN_DASHBOARD_DECISION_KINDS: Final[tuple[str, ...]] = (
    "dashboard_review_decision_approve",
    "dashboard_review_decision_hold",
    "dashboard_review_decision_reject",
    "dashboard_review_decision_defer",
)

DASHBOARD_RECORD_KINDS: Final[tuple[str, ...]] = (
    "dashboard_note",
    *HUMAN_DASHBOARD_DECISION_KINDS,
    "dashboard_snapshot",
)

FORBIDDEN_DASHBOARD_ACTIONS: Final[tuple[tuple[str, str], ...]] = (
    ("automatic_execution", "Never executes platform actions automatically."),
    ("automatic_decision", "Never makes executive decisions automatically."),
    ("automatic_strategy_execution", "Never executes strategy automatically."),
    ("automatic_operational_execution", "Never executes operational changes automatically."),
    ("cross_tenant_dashboard_visibility", "Never aggregates executive signals across tenants."),
)

EXECUTIVE_OPERATING_SYSTEM_DASHBOARD_EXECUTABLE: Final[bool] = False

MAX_DASHBOARD_CONTENT_LEN: Final[int] = 4000
MAX_PERSISTED_DASHBOARD_RECORDS: Final[int] = 500
