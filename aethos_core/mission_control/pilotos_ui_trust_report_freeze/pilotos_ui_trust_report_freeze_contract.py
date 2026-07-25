# SPDX-License-Identifier: Apache-2.0
"""FIX 192 — PilotOS UI trust report freeze contract."""

from __future__ import annotations

from typing import Final

from aethos_core.mission_control.pilotos_ui_pilot_arc_orchestrator.pilotos_ui_pilot_arc_orchestrator_contract import (
    PILOTOS_PILOT_SESSIONS,
    PILOTOS_UI_DEFAULT_REPO_ISSUE,
    PILOTOS_UI_REPOSITORY,
)

PILOTOS_UI_TRUST_REPORT_FREEZE_SCHEMA_VERSION: Final[str] = (
    "mission_control_pilotos_ui_trust_report_freeze_v1"
)
PILOTOS_UI_TRUST_REPORT_FREEZE_RECORD_SCHEMA_VERSION: Final[str] = (
    "mission_control_pilotos_ui_trust_report_freeze_record_v1"
)
PILOTOS_UI_TRUST_REPORT_FREEZE_FIX: Final[str] = "FIX 192"

MUTATION_PERFORMED_FIX_192: Final[bool] = False
EXECUTION_PERFORMED_FIX_192: Final[bool] = False
PILOT_REEXECUTION_PERFORMED_FIX_192: Final[bool] = False
TRUST_GRANTING_AUTHORITY_FIX_192: Final[bool] = False
PILOT_EXECUTION_AUTHORITY_FIX_192: Final[bool] = False
CROSS_REPO_AUTHORITY_FIX_192: Final[bool] = False
AUTOMATIC_EXPANSION_ENABLED_FIX_192: Final[bool] = False
GATE_BYPASS_ENABLED_FIX_192: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_192: Final[bool] = False
ATLAS_EXPANSION_BLOCKED_BY_DEFAULT_FIX_192: Final[bool] = True

TRUST_REPORT_COMPOSES_ARTIFACTS_ONLY_FIX_192: Final[bool] = True
PILOTOS_UI_TRUST_REPORT_FREEZE_ORIGIN: Final[str] = (
    "mission_control_pilotos_ui_trust_report_freeze"
)
PILOTOS_UI_TRUST_REPORT_FREEZE_ROUTE_ID: Final[str] = (
    "mission_control_pilotos_ui_trust_report_freeze"
)

PILOTOS_UI_TRUST_REPORT_FREEZE_INVARIANT: Final[str] = (
    "pilotos_ui_trust_report_freeze_composes_pilotos_pilot_arc_artifacts_without_pilot_reexecution_or_trust_granting"
)

PILOTOS_UI_REPO_ISSUE: Final[str] = PILOTOS_UI_DEFAULT_REPO_ISSUE

TRUST_STATUSES: Final[tuple[str, ...]] = (
    "CONDITIONALLY_TRUSTED",
    "NOT_TRUSTED",
    "TRUST_PENDING",
    "PENDING_EVIDENCE",
)

EXPANSION_RECOMMENDATION_VALUES: Final[tuple[str, ...]] = (
    "DO_NOT_EXPAND",
    "EXPAND_WITH_REVIEW",
    "CONDITIONALLY_EXPAND",
    "ADVISORY_ONLY",
)

HUMAN_TRUST_DECISION_KINDS: Final[tuple[str, ...]] = (
    "human_trust_decision_approve",
    "human_trust_decision_hold",
    "human_trust_decision_reject",
    "human_trust_decision_defer",
)

PILOTOS_UI_TRUST_REPORT_FREEZE_RECORD_KINDS: Final[tuple[str, ...]] = (
    "pilotos_trust_report_freeze_artifact",
    "operator_review_note",
    "trust_boundary_note",
    "intervention_note",
    *HUMAN_TRUST_DECISION_KINDS,
)

PILOTOS_UI_TRUST_REPORT_FREEZE_PRINCIPLES: Final[tuple[tuple[str, str], ...]] = (
    ("trust_freeze_not_trust", "Trust freeze ≠ trust granting."),
    ("compose_only", "Composes FIX 188–191 and FIX 260 — no pilot re-execution."),
    ("repository_scoped", "PilotOS UI trust baseline separate from AethOS FIX 186."),
    ("no_inherited_trust", "AethOS trust never transfers to PilotOS UI."),
    ("human_trust_decision", "Operator records approve/hold/reject/defer — trust remains human."),
    ("atlas_blocked_by_default", "Atlas Trader pilot blocked until PilotOS UI trust freeze complete."),
    ("reproducible_from_artifacts", "Report reproducible from stored audits and receipts."),
    ("advisory_expansion", "Expansion recommendation is advisory only."),
)

FORBIDDEN_PILOTOS_TRUST_FREEZE_ACTIONS: Final[tuple[tuple[str, str], ...]] = (
    ("pilot_execution", "Trust freeze never executes pilot harness."),
    ("trust_granting", "Trust freeze never automatically grants CONDITIONALLY_TRUSTED."),
    ("trust_inheritance", "Trust freeze never inherits AethOS trust."),
    ("cross_repo_authority", "Trust freeze never exercises cross-repo authority."),
    ("repository_mutation", "Trust freeze never mutates repositories."),
    ("code_generation", "Trust freeze never generates code."),
    ("pr_creation", "Trust freeze never creates pull requests."),
    ("merge", "Trust freeze never merges."),
    ("deploy", "Trust freeze never deploys."),
    ("rollback", "Trust freeze never rollbacks."),
    ("gate_bypass", "Trust freeze never bypasses frozen gates."),
)

PILOTOS_UI_TRUST_REPORT_FREEZE_EXECUTABLE: Final[bool] = False

MAX_PILOTOS_UI_TRUST_REPORT_FREEZE_CONTENT_LEN: Final[int] = 4000
MAX_PERSISTED_PILOTOS_UI_TRUST_REPORT_FREEZE_RECORDS: Final[int] = 500

PILOTOS_UI_PILOT_SESSIONS_FIX_192: Final[tuple[str, ...]] = PILOTOS_PILOT_SESSIONS
PILOTOS_UI_REPOSITORY_FIX_192: Final[str] = PILOTOS_UI_REPOSITORY
