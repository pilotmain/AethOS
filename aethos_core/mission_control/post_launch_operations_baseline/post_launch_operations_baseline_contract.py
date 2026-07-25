# SPDX-License-Identifier: Apache-2.0
"""FIX 316 — post-launch operations baseline contract."""

from __future__ import annotations

from typing import Final

POST_LAUNCH_OPERATIONS_BASELINE_SCHEMA_VERSION: Final[str] = (
    "mission_control_post_launch_operations_baseline_v1"
)
POST_LAUNCH_OPERATIONS_BASELINE_RECORD_SCHEMA_VERSION: Final[str] = (
    "mission_control_post_launch_operations_baseline_record_v1"
)
POST_LAUNCH_OPERATIONS_BASELINE_FIX: Final[str] = "FIX 316"

MUTATION_PERFORMED_FIX_316: Final[bool] = False
EXECUTION_PERFORMED_FIX_316: Final[bool] = False
POST_LAUNCH_OPERATIONS_AUTHORITY_FIX_316: Final[bool] = False
AUTOMATIC_OPERATIONAL_EXECUTION_ENABLED_FIX_316: Final[bool] = False
AUTOMATIC_CUSTOMER_CONTACT_ENABLED_FIX_316: Final[bool] = False
AUTOMATIC_INCIDENT_RESPONSE_ENABLED_FIX_316: Final[bool] = False
TRUST_MUTATION_AUTHORITY_FIX_316: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_316: Final[bool] = False
POST_LAUNCH_OPERATIONS_COMPOSES_EVIDENCE_ONLY_FIX_316: Final[bool] = True
PILOT_EXECUTION_PERFORMED_FIX_316: Final[bool] = False

POST_LAUNCH_OPERATIONS_BASELINE_ROUTE_ID: Final[str] = (
    "mission_control_post_launch_operations_baseline"
)

POST_LAUNCH_OPERATIONS_BASELINE_INVARIANT: Final[str] = (
    "post_launch_operations_baseline_without_operational_authority"
)

POST_LAUNCH_OPERATIONS_BASELINE_DOMAINS: Final[tuple[str, ...]] = (
    "platform_health_baseline",
    "customer_health_baseline",
    "governance_health_baseline",
    "incident_baseline",
    "trust_baseline",
    "capability_baseline",
    "commercial_baseline",
    "portfolio_baseline",
    "post_launch_operations_dashboard",
    "operations_baseline_registry",
)

HUMAN_OPERATIONS_BASELINE_DECISION_KINDS: Final[tuple[str, ...]] = (
    "operations_baseline_review_decision_approve",
    "operations_baseline_review_decision_hold",
    "operations_baseline_review_decision_reject",
    "operations_baseline_review_decision_defer",
)

POST_LAUNCH_OPERATIONS_BASELINE_RECORD_KINDS: Final[tuple[str, ...]] = (
    "operations_baseline_note",
    *HUMAN_OPERATIONS_BASELINE_DECISION_KINDS,
    "operations_baseline_record",
    "operations_baseline_snapshot",
)

POST_LAUNCH_OPERATIONS_BASELINE_PRINCIPLES: Final[tuple[tuple[str, str], ...]] = (
    ("baseline_not_authority", "Post-launch operations baseline ≠ operational authority."),
    ("observe_assess_recommend", "AethOS may observe, assess, and recommend — not execute."),
    ("permanent_reference", "Canonical post-launch operating baseline for future assessments."),
    ("compose_only", "Composes FIX 186–315 evidence without recalculation or pilot execution."),
    ("platform_health", "Platform health from FIX 220 and FIX 313 monitoring signals."),
    ("customer_health", "Customer health from FIX 310 and FIX 312 adoption signals."),
    ("governance_health", "Governance health from FIX 302 and FIX 307 audit signals."),
    ("incident_baseline", "Incident baseline from FIX 220, 230, and FIX 313."),
    ("trust_capability_commercial", "Trust, capability, commercial, and portfolio baselines frozen."),
)

FORBIDDEN_POST_LAUNCH_OPERATIONS_ACTIONS: Final[tuple[tuple[str, str], ...]] = (
    ("incident_execution", "Baseline never executes incident response."),
    ("customer_outreach", "Baseline never performs customer outreach."),
    ("deployment_actions", "Baseline never performs deployment actions."),
    ("rollback_actions", "Baseline never performs rollback actions."),
    ("trust_modification", "Baseline never modifies trust."),
    ("provider_mutation", "Baseline never mutates providers."),
    ("autonomous_operations", "Baseline never performs autonomous operational behavior."),
)

POST_LAUNCH_OPERATIONS_BASELINE_EXECUTABLE: Final[bool] = False

MAX_POST_LAUNCH_OPERATIONS_BASELINE_CONTENT_LEN: Final[int] = 4000
MAX_PERSISTED_POST_LAUNCH_OPERATIONS_BASELINE_RECORDS: Final[int] = 500
