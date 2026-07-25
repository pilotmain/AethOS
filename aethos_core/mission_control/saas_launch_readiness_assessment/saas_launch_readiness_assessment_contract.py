# SPDX-License-Identifier: Apache-2.0
"""FIX 309 — SaaS launch readiness assessment contract."""

from __future__ import annotations

from typing import Final

SAAS_LAUNCH_READINESS_ASSESSMENT_SCHEMA_VERSION: Final[str] = (
    "mission_control_saas_launch_readiness_assessment_v1"
)
SAAS_LAUNCH_READINESS_ASSESSMENT_RECORD_SCHEMA_VERSION: Final[str] = (
    "mission_control_saas_launch_readiness_assessment_record_v1"
)
SAAS_LAUNCH_READINESS_ASSESSMENT_FIX: Final[str] = "FIX 309"

MUTATION_PERFORMED_FIX_309: Final[bool] = False
EXECUTION_PERFORMED_FIX_309: Final[bool] = False
LAUNCH_AUTHORITY_FIX_309: Final[bool] = False
AUTOMATIC_LAUNCH_ENABLED_FIX_309: Final[bool] = False
AUTOMATIC_READINESS_PROMOTION_ENABLED_FIX_309: Final[bool] = False
TRUST_MUTATION_AUTHORITY_FIX_309: Final[bool] = False
CUSTOMER_PROVISIONING_AUTHORITY_FIX_309: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_309: Final[bool] = False
LAUNCH_ASSESSMENT_COMPOSES_EVIDENCE_ONLY_FIX_309: Final[bool] = True

SAAS_LAUNCH_READINESS_ASSESSMENT_ROUTE_ID: Final[str] = (
    "mission_control_saas_launch_readiness_assessment"
)

SAAS_LAUNCH_READINESS_ASSESSMENT_INVARIANT: Final[str] = (
    "saas_launch_readiness_assessment_evidence_without_launch_authority"
)

LAUNCH_ASSESSMENT_DOMAINS: Final[tuple[str, ...]] = (
    "product_readiness",
    "platform_readiness",
    "security_readiness",
    "governance_readiness",
    "operational_readiness",
    "commercial_readiness",
    "customer_readiness",
    "support_readiness",
    "launch_risk_registry",
    "launch_readiness_dashboard",
)

DOMAIN_SCORES: Final[tuple[str, ...]] = (
    "NOT_READY",
    "PARTIALLY_READY",
    "READY",
    "LAUNCH_READY",
)

OVERALL_LAUNCH_STATUSES: Final[tuple[str, ...]] = (
    "BLOCKED",
    "CONDITIONAL",
    "READY_FOR_LIMITED_BETA",
    "READY_FOR_PUBLIC_LAUNCH",
)

RISK_LEVELS: Final[tuple[str, ...]] = (
    "critical",
    "high",
    "medium",
    "low",
)

HUMAN_LAUNCH_READINESS_DECISION_KINDS: Final[tuple[str, ...]] = (
    "launch_readiness_decision_approve",
    "launch_readiness_decision_hold",
    "launch_readiness_decision_reject",
    "launch_readiness_decision_defer",
)

SAAS_LAUNCH_READINESS_ASSESSMENT_RECORD_KINDS: Final[tuple[str, ...]] = (
    "launch_readiness_note",
    *HUMAN_LAUNCH_READINESS_DECISION_KINDS,
    "saas_launch_readiness_assessment_record",
)

SAAS_LAUNCH_READINESS_ASSESSMENT_PRINCIPLES: Final[tuple[tuple[str, str], ...]] = (
    ("assessment_not_authority", "Launch assessment ≠ launch authority."),
    ("human_decides", "Humans decide launch readiness — AethOS assesses only."),
    ("evidence_backed", "Readiness derived from FIX 181–308 evidence only."),
    ("no_reexecution", "Composes trust baselines and pilot evidence without re-running pilots."),
    ("blocker_visibility", "Launch blockers and risks visible before external customers."),
    ("tiered_launch", "Overall status may justify limited beta — not automatic launch."),
    ("compose_only", "No customer provisioning, plan activation, or trust mutation."),
    ("risk_registry", "Critical through low risks tracked with evidence references."),
    ("human_review", "Launch readiness review records decisions without declaring launch."),
    ("evidence_over_opinion", "Replaces opinion-based launch decisions with evidence."),
)

FORBIDDEN_LAUNCH_ASSESSMENT_ACTIONS: Final[tuple[tuple[str, str], ...]] = (
    ("launch_declaration", "Assessment never declares AethOS launched."),
    ("customer_provisioning", "Assessment never provisions customers."),
    ("plan_activation", "Assessment never activates plans."),
    ("trust_mutation", "Assessment never mutates trust."),
    ("provider_mutation", "Assessment never mutates providers."),
    ("operational_mutation", "Assessment never mutates operational state."),
    ("automatic_readiness_promotion", "Assessment never promotes readiness automatically."),
    ("hidden_launch_paths", "Assessment never introduces hidden launch paths."),
)

SAAS_LAUNCH_READINESS_ASSESSMENT_EXECUTABLE: Final[bool] = False

MAX_SAAS_LAUNCH_READINESS_ASSESSMENT_CONTENT_LEN: Final[int] = 4000
MAX_PERSISTED_SAAS_LAUNCH_READINESS_ASSESSMENT_RECORDS: Final[int] = 500
