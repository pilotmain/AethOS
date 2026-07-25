# SPDX-License-Identifier: Apache-2.0
"""FIX 196 — Nexora trust report freeze contract."""

from __future__ import annotations

from typing import Final

from aethos_core.mission_control.nexora_pilot_arc_orchestrator.nexora_pilot_arc_orchestrator_contract import (
    NEXORA_DEFAULT_REPO_ISSUE,
    NEXORA_PILOT_SESSIONS,
    NEXORA_REPOSITORY,
)

NEXORA_TRUST_REPORT_FREEZE_SCHEMA_VERSION: Final[str] = "mission_control_nexora_trust_report_freeze_v1"
NEXORA_TRUST_REPORT_FREEZE_RECORD_SCHEMA_VERSION: Final[str] = (
    "mission_control_nexora_trust_report_freeze_record_v1"
)
NEXORA_TRUST_REPORT_FREEZE_FIX: Final[str] = "FIX 196"

MUTATION_PERFORMED_FIX_196: Final[bool] = False
EXECUTION_PERFORMED_FIX_196: Final[bool] = False
PILOT_REEXECUTION_PERFORMED_FIX_196: Final[bool] = False
TRUST_GRANTING_AUTHORITY_FIX_196: Final[bool] = False
TRUST_INHERITANCE_ENABLED_FIX_196: Final[bool] = False
PILOT_EXECUTION_AUTHORITY_FIX_196: Final[bool] = False
CROSS_REPO_AUTHORITY_FIX_196: Final[bool] = False
AUTOMATIC_EXPANSION_ENABLED_FIX_196: Final[bool] = False
GATE_BYPASS_ENABLED_FIX_196: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_196: Final[bool] = False
PROVIDER_MUTATION_ENABLED_FIX_196: Final[bool] = False

TRUST_REPORT_COMPOSES_ARTIFACTS_ONLY_FIX_196: Final[bool] = True
MULTI_REPO_TRUST_BASELINE_PROGRAM_FIX_196: Final[bool] = True
NEXORA_TRUST_REPORT_FREEZE_ORIGIN: Final[str] = "mission_control_nexora_trust_report_freeze"
NEXORA_TRUST_REPORT_FREEZE_ROUTE_ID: Final[str] = "mission_control_nexora_trust_report_freeze"

NEXORA_TRUST_REPORT_FREEZE_INVARIANT: Final[str] = (
    "nexora_trust_report_freeze_composes_nexora_pilot_arc_artifacts_without_pilot_reexecution_or_trust_granting"
)

NEXORA_REPO_ISSUE: Final[str] = NEXORA_DEFAULT_REPO_ISSUE

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

NEXORA_TRUST_REPORT_FREEZE_RECORD_KINDS: Final[tuple[str, ...]] = (
    "nexora_trust_report_freeze_artifact",
    "operator_review_note",
    "trust_boundary_note",
    "intervention_note",
    *HUMAN_TRUST_DECISION_KINDS,
)

NEXORA_TRUST_REPORT_FREEZE_PRINCIPLES: Final[tuple[tuple[str, str], ...]] = (
    ("trust_freeze_not_trust", "Trust freeze ≠ trust granting."),
    ("compose_only", "Composes FIX 195–191 and FIX 260 — no pilot re-execution."),
    ("repository_scoped", "Nexora trust baseline separate from all upstream repositories."),
    ("no_inherited_trust", "AethOS, PilotOS UI, and Atlas Trader trust never transfer to Nexora."),
    ("human_trust_decision", "Operator records approve/hold/reject/defer — trust remains human."),
    ("completes_trust_baseline_program", "Human approval completes the four-repository trust baseline program."),
    ("reproducible_from_artifacts", "Report reproducible from stored audits and receipts."),
    ("advisory_expansion", "Expansion recommendation is advisory only — FIX 261 follows separately."),
)

FORBIDDEN_NEXORA_TRUST_FREEZE_ACTIONS: Final[tuple[tuple[str, str], ...]] = (
    ("pilot_execution", "Trust freeze never executes pilot harness."),
    ("trust_granting", "Trust freeze never automatically grants CONDITIONALLY_TRUSTED."),
    ("trust_inheritance", "Trust freeze never inherits upstream repository trust."),
    ("cross_repo_authority", "Trust freeze never exercises cross-repo authority."),
    ("repository_mutation", "Trust freeze never mutates repositories."),
    ("code_generation", "Trust freeze never generates code."),
    ("pr_creation", "Trust freeze never creates pull requests."),
    ("merge", "Trust freeze never merges."),
    ("deploy", "Trust freeze never deploys."),
    ("rollback", "Trust freeze never rollbacks."),
    ("provider_mutation", "Trust freeze never mutates providers."),
    ("gate_bypass", "Trust freeze never bypasses frozen gates."),
)

NEXORA_TRUST_REPORT_FREEZE_EXECUTABLE: Final[bool] = False

MAX_NEXORA_TRUST_REPORT_FREEZE_CONTENT_LEN: Final[int] = 4000
MAX_PERSISTED_NEXORA_TRUST_REPORT_FREEZE_RECORDS: Final[int] = 500

NEXORA_PILOT_SESSIONS_FIX_196: Final[tuple[str, ...]] = NEXORA_PILOT_SESSIONS
NEXORA_REPOSITORY_FIX_196: Final[str] = NEXORA_REPOSITORY
