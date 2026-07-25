# SPDX-License-Identifier: Apache-2.0
"""FIX 194 — Atlas Trader trust report freeze contract."""

from __future__ import annotations

from typing import Final

from aethos_core.mission_control.atlas_trader_pilot_arc_orchestrator.atlas_trader_pilot_arc_orchestrator_contract import (
    ATLAS_PILOT_SESSIONS,
    ATLAS_TRADER_DEFAULT_REPO_ISSUE,
    ATLAS_TRADER_REPOSITORY,
)

ATLAS_TRADER_TRUST_REPORT_FREEZE_SCHEMA_VERSION: Final[str] = (
    "mission_control_atlas_trader_trust_report_freeze_v1"
)
ATLAS_TRADER_TRUST_REPORT_FREEZE_RECORD_SCHEMA_VERSION: Final[str] = (
    "mission_control_atlas_trader_trust_report_freeze_record_v1"
)
ATLAS_TRADER_TRUST_REPORT_FREEZE_FIX: Final[str] = "FIX 194"

MUTATION_PERFORMED_FIX_194: Final[bool] = False
EXECUTION_PERFORMED_FIX_194: Final[bool] = False
PILOT_REEXECUTION_PERFORMED_FIX_194: Final[bool] = False
TRUST_GRANTING_AUTHORITY_FIX_194: Final[bool] = False
TRUST_INHERITANCE_ENABLED_FIX_194: Final[bool] = False
PILOT_EXECUTION_AUTHORITY_FIX_194: Final[bool] = False
CROSS_REPO_AUTHORITY_FIX_194: Final[bool] = False
AUTOMATIC_EXPANSION_ENABLED_FIX_194: Final[bool] = False
GATE_BYPASS_ENABLED_FIX_194: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_194: Final[bool] = False
NEXORA_EXPANSION_BLOCKED_BY_DEFAULT_FIX_194: Final[bool] = True

TRUST_REPORT_COMPOSES_ARTIFACTS_ONLY_FIX_194: Final[bool] = True
ATLAS_TRADER_TRUST_REPORT_FREEZE_ORIGIN: Final[str] = (
    "mission_control_atlas_trader_trust_report_freeze"
)
ATLAS_TRADER_TRUST_REPORT_FREEZE_ROUTE_ID: Final[str] = (
    "mission_control_atlas_trader_trust_report_freeze"
)

ATLAS_TRADER_TRUST_REPORT_FREEZE_INVARIANT: Final[str] = (
    "atlas_trader_trust_report_freeze_composes_atlas_pilot_arc_artifacts_without_pilot_reexecution_or_trust_granting"
)

ATLAS_TRADER_REPO_ISSUE: Final[str] = ATLAS_TRADER_DEFAULT_REPO_ISSUE

TRUST_STATUSES: Final[tuple[str, ...]] = (
    "CONDITIONALLY_TRUSTED",
    "TRUST_REVIEW_PENDING",
    "NOT_TRUSTED",
    "UNPROVEN",
)

EXPANSION_RECOMMENDATION_VALUES: Final[tuple[str, ...]] = (
    "DO_NOT_EXPAND",
    "EXPAND_WITH_REVIEW",
    "CONDITIONALLY_EXPAND",
)

HUMAN_TRUST_DECISION_KINDS: Final[tuple[str, ...]] = (
    "human_trust_decision_approve",
    "human_trust_decision_hold",
    "human_trust_decision_reject",
    "human_trust_decision_defer",
)

ATLAS_TRADER_TRUST_REPORT_FREEZE_RECORD_KINDS: Final[tuple[str, ...]] = (
    "atlas_trust_report_freeze_artifact",
    "operator_review_note",
    "trust_boundary_note",
    "intervention_note",
    *HUMAN_TRUST_DECISION_KINDS,
)

ATLAS_TRADER_TRUST_REPORT_FREEZE_PRINCIPLES: Final[tuple[tuple[str, str], ...]] = (
    ("trust_freeze_not_trust", "Trust freeze ≠ trust granting."),
    ("compose_only", "Composes FIX 193–191 and FIX 260 — no pilot re-execution."),
    ("repository_scoped", "Atlas Trader trust baseline separate from AethOS and PilotOS UI."),
    ("no_inherited_trust", "PilotOS UI and AethOS trust never transfer to Atlas Trader."),
    ("human_trust_decision", "Operator records approve/hold/reject/defer — trust remains human."),
    ("nexora_blocked_by_default", "Nexora pilot blocked until Atlas Trader trust freeze complete."),
    ("reproducible_from_artifacts", "Report reproducible from stored audits and receipts."),
    ("advisory_expansion", "Expansion recommendation is advisory only."),
)

FORBIDDEN_ATLAS_TRUST_FREEZE_ACTIONS: Final[tuple[tuple[str, str], ...]] = (
    ("pilot_execution", "Trust freeze never executes pilot harness."),
    ("trust_granting", "Trust freeze never automatically grants CONDITIONALLY_TRUSTED."),
    ("trust_inheritance", "Trust freeze never inherits AethOS or PilotOS UI trust."),
    ("cross_repo_authority", "Trust freeze never exercises cross-repo authority."),
    ("repository_mutation", "Trust freeze never mutates repositories."),
    ("code_generation", "Trust freeze never generates code."),
    ("pr_creation", "Trust freeze never creates pull requests."),
    ("merge", "Trust freeze never merges."),
    ("deploy", "Trust freeze never deploys."),
    ("rollback", "Trust freeze never rollbacks."),
    ("gate_bypass", "Trust freeze never bypasses frozen gates."),
)

ATLAS_TRADER_TRUST_REPORT_FREEZE_EXECUTABLE: Final[bool] = False

MAX_ATLAS_TRADER_TRUST_REPORT_FREEZE_CONTENT_LEN: Final[int] = 4000
MAX_PERSISTED_ATLAS_TRADER_TRUST_REPORT_FREEZE_RECORDS: Final[int] = 500

ATLAS_PILOT_SESSIONS_FIX_194: Final[tuple[str, ...]] = ATLAS_PILOT_SESSIONS
ATLAS_TRADER_REPOSITORY_FIX_194: Final[str] = ATLAS_TRADER_REPOSITORY
