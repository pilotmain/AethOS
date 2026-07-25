# SPDX-License-Identifier: Apache-2.0
"""FIX 313 — launch operations center contract."""

from __future__ import annotations

from typing import Final

LAUNCH_OPERATIONS_CENTER_SCHEMA_VERSION: Final[str] = "mission_control_launch_operations_center_v1"
LAUNCH_OPERATIONS_CENTER_RECORD_SCHEMA_VERSION: Final[str] = (
    "mission_control_launch_operations_center_record_v1"
)
LAUNCH_OPERATIONS_CENTER_FIX: Final[str] = "FIX 313"

MUTATION_PERFORMED_FIX_313: Final[bool] = False
EXECUTION_PERFORMED_FIX_313: Final[bool] = False
LAUNCH_OPERATIONS_AUTHORITY_FIX_313: Final[bool] = False
AUTOMATIC_LAUNCH_ENABLED_FIX_313: Final[bool] = False
AUTOMATIC_BETA_EXPANSION_ENABLED_FIX_313: Final[bool] = False
AUTOMATIC_CUSTOMER_ADMISSION_ENABLED_FIX_313: Final[bool] = False
AUTOMATIC_PROVIDER_MUTATION_ENABLED_FIX_313: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_313: Final[bool] = False
LAUNCH_OPERATIONS_COMPOSES_EVIDENCE_ONLY_FIX_313: Final[bool] = True

LAUNCH_OPERATIONS_CENTER_ROUTE_ID: Final[str] = "mission_control_launch_operations_center"

LAUNCH_OPERATIONS_CENTER_INVARIANT: Final[str] = (
    "launch_operations_visibility_without_launch_authority"
)

LAUNCH_OPERATIONS_DOMAINS: Final[tuple[str, ...]] = (
    "launch_status_registry",
    "launch_blocker_registry",
    "launch_risk_dashboard",
    "beta_operations_monitor",
    "customer_operations_monitor",
    "platform_operations_monitor",
    "provider_operations_monitor",
    "launch_evidence_registry",
    "launch_recommendation",
    "launch_operations_dashboard",
)

LAUNCH_RECOMMENDATIONS: Final[tuple[str, ...]] = (
    "BLOCK_LAUNCH",
    "CONTINUE_BETA",
    "EXPAND_BETA",
    "PREPARE_PUBLIC_REVIEW",
    "READY_FOR_LAUNCH_REVIEW",
)

LAUNCH_PHASES: Final[tuple[str, ...]] = (
    "PRE_LAUNCH",
    "LIMITED_BETA",
    "BETA_EXPANSION",
    "PUBLIC_REVIEW",
    "LAUNCH_REVIEW",
)

HUMAN_LAUNCH_OPERATIONS_DECISION_KINDS: Final[tuple[str, ...]] = (
    "launch_operations_review_decision_approve",
    "launch_operations_review_decision_hold",
    "launch_operations_review_decision_reject",
    "launch_operations_review_decision_defer",
)

LAUNCH_OPERATIONS_CENTER_RECORD_KINDS: Final[tuple[str, ...]] = (
    "launch_operations_note",
    *HUMAN_LAUNCH_OPERATIONS_DECISION_KINDS,
    "launch_operations_center_record",
)

LAUNCH_OPERATIONS_CENTER_PRINCIPLES: Final[tuple[tuple[str, str], ...]] = (
    ("visibility_not_authority", "Launch operations visibility ≠ launch authority."),
    ("human_decides", "Humans remain responsible for launch decisions."),
    ("unified_truth", "Single operational truth source for launch readiness."),
    ("compose_only", "Composes FIX 309–312 and lifecycle evidence without execution."),
    ("blocker_aggregation", "Launch blockers aggregated from readiness and beta modules."),
    ("risk_aggregation", "Product, operational, governance, and customer risks unified."),
    ("beta_monitoring", "Beta operations monitor composes FIX 312 cohort and success signals."),
    ("customer_monitoring", "Customer operations monitor composes FIX 310 health signals."),
    ("platform_monitoring", "Platform operations monitor composes FIX 200–230 lifecycle health."),
    ("evidence_recommendation", "Launch recommendation derived from evidence — not launch execution."),
)

FORBIDDEN_LAUNCH_OPERATIONS_ACTIONS: Final[tuple[tuple[str, str], ...]] = (
    ("launch_execution", "Launch operations center never executes launch."),
    ("customer_provisioning", "Launch operations center never provisions customers."),
    ("beta_expansion", "Launch operations center never expands beta automatically."),
    ("provider_mutation", "Launch operations center never mutates providers."),
    ("trust_mutation", "Launch operations center never mutates trust."),
    ("operational_mutation", "Launch operations center never mutates operational state."),
    ("automatic_launch_activity", "Launch operations center never performs automatic launch activity."),
)

LAUNCH_OPERATIONS_CENTER_EXECUTABLE: Final[bool] = False

MAX_LAUNCH_OPERATIONS_CENTER_CONTENT_LEN: Final[int] = 4000
MAX_PERSISTED_LAUNCH_OPERATIONS_CENTER_RECORDS: Final[int] = 500
