# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_F1 / FIX 347 — first customer delivery pilot program contract."""

from __future__ import annotations

from typing import Any, Final

FIRST_CUSTOMER_DELIVERY_PILOT_PROGRAM_ID: Final[str] = "WORKSTREAM_F1"
FIRST_CUSTOMER_DELIVERY_PILOT_PROGRAM_FIX: Final[str] = "FIX 347"
FIRST_CUSTOMER_DELIVERY_PILOT_PROGRAM_SCHEMA_VERSION: Final[str] = (
    "workstream_first_customer_delivery_pilot_program_v1"
)
FIRST_CUSTOMER_DELIVERY_PILOT_PROGRAM_RECORD_SCHEMA_VERSION: Final[str] = (
    "workstream_first_customer_delivery_pilot_program_record_v1"
)

CORE_PRINCIPLE: Final[str] = (
    "customer_delivery_pilot_executes_within_approved_bounds_without_customer_authority"
)

MUTATION_PERFORMED_FIX_347: Final[bool] = False
EXECUTION_PERFORMED_FIX_347: Final[bool] = True
CUSTOMER_AUTHORITY_FIX_347: Final[bool] = False
TRUST_MUTATION_AUTHORITY_FIX_347: Final[bool] = False
AUTHORITY_EXPANSION_FIX_347: Final[bool] = False
AUTOMATIC_CUSTOMER_ACCEPTANCE_FIX_347: Final[bool] = False
GOVERNANCE_BYPASS_AUTHORITY_FIX_347: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_347: Final[bool] = False
LOCAL_CUSTOMER_PILOT_EXECUTABLE_FIX_347: Final[bool] = True

FIRST_CUSTOMER_DELIVERY_PILOT_PROGRAM_ROUTE_ID: Final[str] = (
    "workstream_first_customer_delivery_pilot_program"
)

FIRST_CUSTOMER_DELIVERY_PILOT_PROGRAM_INVARIANT: Final[str] = (
    "first_customer_delivery_pilot_without_customer_authority_or_automatic_acceptance"
)

FIRST_CUSTOMER_DELIVERY_PILOT_PHASES: Final[tuple[str, ...]] = (
    "phase_1_customer_request_intake",
    "phase_2_delivery_planning",
    "phase_3_workspace_creation",
    "phase_4_code_generation",
    "phase_5_git_delivery",
    "phase_6_deployment",
    "phase_7_end_to_end_certification",
    "phase_8_customer_feedback",
    "phase_9_value_realization",
    "phase_10_pilot_review",
)

RECOMMENDED_PILOT_REQUEST_TYPES: Final[tuple[str, ...]] = (
    "fastapi_microservice",
    "nextjs_landing_page",
    "health_check_endpoint",
    "admin_dashboard",
    "automation_utility",
)

PILOT_REQUEST_SCENARIOS: Final[dict[str, str]] = {
    "fastapi_microservice": "scenario_1_fastapi_railway",
    "nextjs_landing_page": "scenario_3_nextjs_vercel",
    "health_check_endpoint": "scenario_1_fastapi_railway",
    "admin_dashboard": "scenario_3_nextjs_vercel",
    "automation_utility": "scenario_5_documentation_change",
}

PILOT_REQUEST_LABELS: Final[dict[str, str]] = {
    "fastapi_microservice": "FastAPI microservice",
    "nextjs_landing_page": "Next.js landing page",
    "health_check_endpoint": "Health-check endpoint",
    "admin_dashboard": "Lightweight admin dashboard",
    "automation_utility": "Small automation utility",
}

PILOT_AVOID: Final[tuple[str, ...]] = (
    "production_critical_systems",
    "sensitive_data",
    "regulated_workloads",
    "payment_flows",
    "destructive_actions",
)

PILOT_METRICS: Final[tuple[str, ...]] = (
    "time_to_workspace_ms",
    "time_to_code_ms",
    "time_to_pr_ms",
    "time_to_deploy_ms",
    "verification_outcome",
    "human_approval_count",
    "intervention_count",
    "customer_satisfaction",
    "value_realized",
)

EXECUTIVE_FIX_MODULES: Final[tuple[str, ...]] = (
    "FIX 316",
    "FIX 324",
    "FIX 329",
    "FIX 330",
)

HUMAN_CUSTOMER_PILOT_DECISION_KINDS: Final[tuple[str, ...]] = (
    "customer_pilot_review_approve",
    "customer_pilot_review_hold",
    "customer_pilot_review_reject",
    "customer_pilot_review_defer",
)

FIRST_CUSTOMER_DELIVERY_PILOT_RECORD_KINDS: Final[tuple[str, ...]] = (
    "customer_delivery_request",
    "customer_pilot_note",
    *HUMAN_CUSTOMER_PILOT_DECISION_KINDS,
    "customer_pilot_executed_note",
    "first_customer_delivery_pilot_record",
)

PROGRAM_NON_GOALS: Final[tuple[str, ...]] = (
    "no_enterprise_onboarding",
    "no_sensitive_data_processing",
    "no_destructive_provider_actions",
    "no_autonomous_scope_expansion",
    "no_production_critical_deployment",
    "no_automatic_customer_acceptance",
)

FORBIDDEN_PILOT_ACTIONS: Final[tuple[tuple[str, str], ...]] = (
    ("customer_authority", "Never grant customer authority from pilot execution."),
    ("automatic_acceptance", "Never accept delivery automatically for the customer."),
    ("scope_expansion", "Never expand pilot scope autonomously."),
    ("governance_bypass", "Never bypass ET1–ET5 governance gates."),
    ("destructive_actions", "Never perform destructive provider actions in pilot."),
)

MAX_FIRST_CUSTOMER_DELIVERY_PILOT_CONTENT_LEN: Final[int] = 8000
MAX_PERSISTED_FIRST_CUSTOMER_DELIVERY_PILOT_RECORDS: Final[int] = 500

DEFAULT_PILOT_REQUEST_TYPE: Final[str] = "health_check_endpoint"
