# SPDX-License-Identifier: Apache-2.0
"""FIX 315 — launch decision package contract."""

from __future__ import annotations

from typing import Final

LAUNCH_DECISION_PACKAGE_SCHEMA_VERSION: Final[str] = "mission_control_launch_decision_package_v1"
LAUNCH_DECISION_PACKAGE_RECORD_SCHEMA_VERSION: Final[str] = (
    "mission_control_launch_decision_package_record_v1"
)
LAUNCH_DECISION_PACKAGE_FIX: Final[str] = "FIX 315"

MUTATION_PERFORMED_FIX_315: Final[bool] = False
EXECUTION_PERFORMED_FIX_315: Final[bool] = False
LAUNCH_DECISION_AUTHORITY_FIX_315: Final[bool] = False
AUTOMATIC_LAUNCH_APPROVAL_ENABLED_FIX_315: Final[bool] = False
AUTOMATIC_LAUNCH_ENABLED_FIX_315: Final[bool] = False
AUTOMATIC_BETA_EXPANSION_ENABLED_FIX_315: Final[bool] = False
TRUST_MUTATION_AUTHORITY_FIX_315: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_315: Final[bool] = False
LAUNCH_DECISION_PACKAGE_COMPOSES_EVIDENCE_ONLY_FIX_315: Final[bool] = True
PILOT_EXECUTION_PERFORMED_FIX_315: Final[bool] = False

LAUNCH_DECISION_PACKAGE_ROUTE_ID: Final[str] = "mission_control_launch_decision_package"

LAUNCH_DECISION_PACKAGE_INVARIANT: Final[str] = (
    "launch_decision_package_without_launch_decision_authority"
)

LAUNCH_DECISION_PACKAGE_DOMAINS: Final[tuple[str, ...]] = (
    "launch_executive_summary",
    "launch_capability_summary",
    "launch_trust_evidence_summary",
    "launch_operational_summary",
    "launch_customer_summary",
    "launch_risk_summary",
    "launch_blocker_summary",
    "launch_recommendation_package",
    "launch_decision_registry",
    "launch_decision_dashboard",
)

LAUNCH_RECOMMENDATION_PACKAGE_VALUES: Final[tuple[str, ...]] = (
    "DO_NOT_PROCEED",
    "LIMITED_BETA_ONLY",
    "EXPAND_BETA",
    "PUBLIC_REVIEW_READY",
    "READY_FOR_LAUNCH_DECISION",
)

HUMAN_LAUNCH_DECISION_KINDS: Final[tuple[str, ...]] = (
    "launch_decision_approve",
    "launch_decision_hold",
    "launch_decision_reject",
    "launch_decision_defer",
)

LAUNCH_DECISION_PACKAGE_RECORD_KINDS: Final[tuple[str, ...]] = (
    "launch_decision_note",
    *HUMAN_LAUNCH_DECISION_KINDS,
    "launch_decision_package_record",
)

LAUNCH_DECISION_PACKAGE_PRINCIPLES: Final[tuple[tuple[str, str], ...]] = (
    ("package_not_decision", "Launch decision package ≠ launch decision."),
    ("human_approves", "Humans remain responsible for launch approval."),
    ("final_review", "Final review package before beta expansion or public launch decision."),
    ("compose_only", "Composes FIX 186–314 evidence without recalculation or pilot execution."),
    ("executive_summary", "Executive summary from FIX 314 frozen baseline."),
    ("capability_summary", "Capability summary from FIX 295, 296, and FIX 314."),
    ("trust_evidence", "Trust and evidence summary from FIX 186–196 and FIX 314."),
    ("operational_readiness", "Operational readiness from FIX 200–230, 313, and 314."),
    ("customer_readiness", "Customer readiness from FIX 310–312."),
    ("recommendation_evidence", "Launch recommendation derived from frozen evidence only."),
)

FORBIDDEN_LAUNCH_DECISION_ACTIONS: Final[tuple[tuple[str, str], ...]] = (
    ("launch_approval", "Launch decision package never approves launch."),
    ("launch_execution", "Launch decision package never executes launch."),
    ("customer_provisioning", "Launch decision package never provisions customers."),
    ("beta_expansion", "Launch decision package never expands beta."),
    ("trust_mutation", "Launch decision package never mutates trust."),
    ("provider_mutation", "Launch decision package never mutates providers."),
    ("automatic_launch", "Launch decision package never performs automatic launch behavior."),
)

LAUNCH_DECISION_PACKAGE_EXECUTABLE: Final[bool] = False

MAX_LAUNCH_DECISION_PACKAGE_CONTENT_LEN: Final[int] = 4000
MAX_PERSISTED_LAUNCH_DECISION_PACKAGE_RECORDS: Final[int] = 500
