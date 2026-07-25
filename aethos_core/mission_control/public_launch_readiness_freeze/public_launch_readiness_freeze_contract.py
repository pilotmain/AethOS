# SPDX-License-Identifier: Apache-2.0
"""FIX 314 — public launch readiness freeze contract."""

from __future__ import annotations

from typing import Final

PUBLIC_LAUNCH_READINESS_FREEZE_SCHEMA_VERSION: Final[str] = (
    "mission_control_public_launch_readiness_freeze_v1"
)
PUBLIC_LAUNCH_READINESS_FREEZE_RECORD_SCHEMA_VERSION: Final[str] = (
    "mission_control_public_launch_readiness_freeze_record_v1"
)
PUBLIC_LAUNCH_READINESS_FREEZE_FIX: Final[str] = "FIX 314"

MUTATION_PERFORMED_FIX_314: Final[bool] = False
EXECUTION_PERFORMED_FIX_314: Final[bool] = False
LAUNCH_FREEZE_AUTHORITY_FIX_314: Final[bool] = False
AUTOMATIC_LAUNCH_ENABLED_FIX_314: Final[bool] = False
AUTOMATIC_BETA_EXPANSION_ENABLED_FIX_314: Final[bool] = False
TRUST_MUTATION_AUTHORITY_FIX_314: Final[bool] = False
LAUNCH_DECISION_AUTHORITY_FIX_314: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_314: Final[bool] = False
LAUNCH_READINESS_FREEZE_COMPOSES_EVIDENCE_ONLY_FIX_314: Final[bool] = True
PILOT_REEXECUTION_PERFORMED_FIX_314: Final[bool] = False

PUBLIC_LAUNCH_READINESS_FREEZE_ROUTE_ID: Final[str] = (
    "mission_control_public_launch_readiness_freeze"
)

PUBLIC_LAUNCH_READINESS_FREEZE_INVARIANT: Final[str] = (
    "launch_readiness_freeze_without_launch_authority"
)

LAUNCH_READINESS_FREEZE_DOMAINS: Final[tuple[str, ...]] = (
    "launch_evidence_timeline",
    "launch_trust_baseline_summary",
    "launch_capability_baseline",
    "launch_operational_baseline",
    "launch_product_baseline",
    "launch_customer_baseline",
    "launch_risk_freeze",
    "launch_blocker_freeze",
    "launch_recommendation_freeze",
    "launch_readiness_freeze_dashboard",
)

LAUNCH_RECOMMENDATION_FREEZE_VALUES: Final[tuple[str, ...]] = (
    "NOT_READY",
    "LIMITED_BETA_READY",
    "PUBLIC_REVIEW_READY",
    "READY_FOR_LAUNCH_DECISION",
)

HUMAN_LAUNCH_FREEZE_DECISION_KINDS: Final[tuple[str, ...]] = (
    "launch_freeze_review_decision_approve",
    "launch_freeze_review_decision_hold",
    "launch_freeze_review_decision_reject",
    "launch_freeze_review_decision_defer",
)

PUBLIC_LAUNCH_READINESS_FREEZE_RECORD_KINDS: Final[tuple[str, ...]] = (
    "launch_freeze_note",
    *HUMAN_LAUNCH_FREEZE_DECISION_KINDS,
    "public_launch_readiness_freeze_record",
)

PUBLIC_LAUNCH_READINESS_FREEZE_PRINCIPLES: Final[tuple[tuple[str, str], ...]] = (
    ("freeze_not_authority", "Launch readiness freeze ≠ launch authority."),
    ("human_decides", "Humans remain responsible for launch decisions."),
    ("official_baseline", "Official launch evidence baseline before beta expansion or public launch."),
    ("compose_only", "Composes FIX 186–313 evidence without re-execution or pilot reruns."),
    ("proven_vs_unproven", "Separates what has been proven from what remains unproven."),
    ("trust_baseline", "Trust freezes from AethOS, PilotOS UI, Atlas Trader, and Nexora summarized."),
    ("capability_baseline", "Capability baseline from FIX 295 and FIX 296 frozen for review."),
    ("operational_baseline", "Operational baseline from FIX 200–230 lifecycle modules."),
    ("risk_blocker_freeze", "Launch risks and blockers frozen from FIX 309 and FIX 313."),
    ("recommendation_evidence", "Launch recommendation derived from frozen evidence only."),
)

FORBIDDEN_LAUNCH_FREEZE_ACTIONS: Final[tuple[tuple[str, str], ...]] = (
    ("launch_execution", "Launch freeze never executes launch."),
    ("customer_provisioning", "Launch freeze never provisions customers."),
    ("trust_mutation", "Launch freeze never mutates trust."),
    ("provider_mutation", "Launch freeze never mutates providers."),
    ("beta_expansion", "Launch freeze never expands beta."),
    ("readiness_promotion", "Launch freeze never promotes readiness automatically."),
    ("automatic_launch", "Launch freeze never performs automatic launch behavior."),
)

PUBLIC_LAUNCH_READINESS_FREEZE_EXECUTABLE: Final[bool] = False

MAX_PUBLIC_LAUNCH_READINESS_FREEZE_CONTENT_LEN: Final[int] = 4000
MAX_PERSISTED_PUBLIC_LAUNCH_READINESS_FREEZE_RECORDS: Final[int] = 500
