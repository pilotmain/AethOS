# SPDX-License-Identifier: Apache-2.0
"""FIX 290 — autonomous business operating system contract."""

from __future__ import annotations

from typing import Final

AUTONOMOUS_BUSINESS_OPERATING_SYSTEM_SCHEMA_VERSION: Final[str] = (
    "mission_control_autonomous_business_operating_system_v1"
)
AUTONOMOUS_BUSINESS_OPERATING_SYSTEM_RECORD_SCHEMA_VERSION: Final[str] = (
    "mission_control_autonomous_business_operating_system_record_v1"
)
AUTONOMOUS_BUSINESS_OPERATING_SYSTEM_FIX: Final[str] = "FIX 290"

MUTATION_PERFORMED_FIX_290: Final[bool] = False
EXECUTION_PERFORMED_FIX_290: Final[bool] = False
BUSINESS_AUTHORITY_FIX_290: Final[bool] = False
AUTOMATIC_BUSINESS_EXECUTION_ENABLED_FIX_290: Final[bool] = False
CUSTOMER_MUTATION_AUTHORITY_FIX_290: Final[bool] = False
BILLING_AUTHORITY_FIX_290: Final[bool] = False
REPOSITORY_MUTATION_AUTHORITY_FIX_290: Final[bool] = False
DEPLOYMENT_AUTHORITY_FIX_290: Final[bool] = False
ROLLBACK_AUTHORITY_FIX_290: Final[bool] = False
TRUST_MUTATION_AUTHORITY_FIX_290: Final[bool] = False
MERGE_AUTHORITY_FIX_290: Final[bool] = False
PROVIDER_MUTATION_AUTHORITY_FIX_290: Final[bool] = False
GATE_BYPASS_ENABLED_FIX_290: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_290: Final[bool] = False
AUTONOMOUS_BUSINESS_OPERATING_COMPOSES_EVIDENCE_ONLY_FIX_290: Final[bool] = True

AUTONOMOUS_BUSINESS_OPERATING_SYSTEM_ROUTE_ID: Final[str] = (
    "mission_control_autonomous_business_operating_system"
)
AUTONOMOUS_BUSINESS_OPERATING_SYSTEM_ORIGIN: Final[str] = (
    "mission_control_autonomous_business_operating_system"
)

AUTONOMOUS_BUSINESS_OPERATING_SYSTEM_INVARIANT: Final[str] = (
    "autonomous_business_operating_system_understands_business_without_business_authority"
)

BUSINESS_DOMAINS: Final[tuple[str, ...]] = (
    "product",
    "customer",
    "revenue",
    "team",
    "project",
    "operational",
)

BUSINESS_HEALTH_DIMENSIONS: Final[tuple[str, ...]] = (
    "product",
    "customer",
    "revenue",
    "delivery",
    "operational",
    "portfolio",
)

BUSINESS_RISK_DIMENSIONS: Final[tuple[str, ...]] = (
    "delivery",
    "operational",
    "customer",
    "revenue",
    "strategic",
)

HUMAN_BUSINESS_DECISION_KINDS: Final[tuple[str, ...]] = (
    "human_business_decision_approve",
    "human_business_decision_hold",
    "human_business_decision_reject",
    "human_business_decision_defer",
)

AUTONOMOUS_BUSINESS_OPERATING_SYSTEM_RECORD_KINDS: Final[tuple[str, ...]] = (
    "product_domain_note",
    "customer_domain_note",
    "revenue_domain_note",
    "team_domain_note",
    "project_domain_note",
    "operational_domain_note",
    "business_goal_note",
    "strategic_alignment_note",
    "customer_insight_note",
    "revenue_observation_note",
    *HUMAN_BUSINESS_DECISION_KINDS,
    "autonomous_business_operating_system_record",
)

AUTONOMOUS_BUSINESS_OPERATING_SYSTEM_PRINCIPLES: Final[tuple[tuple[str, str], ...]] = (
    ("business_not_authority", "Business operating system ≠ business authority."),
    ("compose_only", "Composes FIX 260–280 without re-execution."),
    ("unified_model", "One operating model spans customers, revenue, teams, and products."),
    ("humans_run_business", "Humans run the business — governed systems execute approved work."),
    ("no_financial_transactions", "No financial transactions from business operating layer."),
    ("no_customer_mutation", "No customer mutations from business operating layer."),
    ("no_billing_execution", "No billing execution from business operating layer."),
    ("no_repository_mutation", "No repository mutation from business operating layer."),
    ("strategic_alignment", "Strategic alignment connects goals to delivery work."),
    ("advisory_opportunities", "Business opportunity portfolio aggregates lifecycle and operator signals."),
    ("memory_persistence", "Business operating memory persists goals, decisions, and observations."),
)

FORBIDDEN_BUSINESS_OPERATING_ACTIONS: Final[tuple[tuple[str, str], ...]] = (
    ("financial_transactions", "Business operating system never executes financial transactions."),
    ("customer_mutation", "Business operating system never mutates customer records."),
    ("billing_execution", "Business operating system never executes billing."),
    ("repository_mutation", "Business operating system never mutates repositories."),
    ("code_execution", "Business operating system never executes code."),
    ("pr_creation", "Business operating system never creates pull requests."),
    ("merge_execution", "Business operating system never merges."),
    ("deploy_execution", "Business operating system never deploys."),
    ("provider_mutation", "Business operating system never mutates providers."),
    ("trust_mutation", "Business operating system never mutates trust baselines."),
    ("cross_system_execution", "Business operating system never executes cross-system changes."),
    ("automatic_business_execution", "Business operating system never auto-executes business actions."),
    ("gate_bypass", "Business operating system never bypasses frozen governance gates."),
)

AUTONOMOUS_BUSINESS_OPERATING_SYSTEM_EXECUTABLE: Final[bool] = False

MAX_AUTONOMOUS_BUSINESS_OPERATING_SYSTEM_CONTENT_LEN: Final[int] = 4000
MAX_PERSISTED_AUTONOMOUS_BUSINESS_OPERATING_SYSTEM_RECORDS: Final[int] = 500
