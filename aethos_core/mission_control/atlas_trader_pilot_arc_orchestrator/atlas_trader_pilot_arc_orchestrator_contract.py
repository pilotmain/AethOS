# SPDX-License-Identifier: Apache-2.0
"""FIX 193 — Atlas Trader pilot arc orchestrator contract."""

from __future__ import annotations

from typing import Final

ATLAS_TRADER_PILOT_ARC_ORCHESTRATOR_SCHEMA_VERSION: Final[str] = (
    "mission_control_atlas_trader_pilot_arc_orchestrator_v1"
)
ATLAS_TRADER_PILOT_ARC_ORCHESTRATOR_RECORD_SCHEMA_VERSION: Final[str] = (
    "mission_control_atlas_trader_pilot_arc_orchestrator_record_v1"
)
ATLAS_TRADER_PILOT_ARC_ORCHESTRATOR_FIX: Final[str] = "FIX 193"

ATLAS_TRADER_REPOSITORY: Final[str] = "pilotmain/atlas-trader"
ATLAS_TRADER_DEFAULT_REPO_ISSUE: Final[str] = "pilotmain/atlas-trader#1"

ATLAS_PILOT_SESSIONS: Final[tuple[str, ...]] = (
    "atlas-pilot-1",
    "atlas-pilot-2",
    "atlas-pilot-3",
)

PILOT_ARC_STATES: Final[tuple[str, ...]] = (
    "UNPROVEN",
    "PILOT_1_READY",
    "PILOT_1_RUNNING",
    "PILOT_1_COMPLETE",
    "PILOT_2_RUNNING",
    "PILOT_2_COMPLETE",
    "PILOT_3_RUNNING",
    "PILOT_3_COMPLETE",
    "TRUST_REVIEW_PENDING",
    "CONDITIONALLY_TRUSTED",
)

TRUST_RECOMMENDATION_STATUSES: Final[tuple[str, ...]] = (
    "NOT_READY",
    "PILOTING",
    "TRUST_REVIEW_PENDING",
)

MUTATION_PERFORMED_FIX_193: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_193: Final[bool] = False
TRUST_GRANTING_AUTHORITY_FIX_193: Final[bool] = False
TRUST_INHERITANCE_ENABLED_FIX_193: Final[bool] = False
CROSS_REPO_AUTHORITY_FIX_193: Final[bool] = False
PILOT_EXECUTION_BYPASS_ENABLED_FIX_193: Final[bool] = False
HIDDEN_PILOT_EXECUTION_ENABLED_FIX_193: Final[bool] = False
GATE_BYPASS_ENABLED_FIX_193: Final[bool] = False
MERGE_AUTHORITY_FIX_193: Final[bool] = False
DEPLOY_AUTHORITY_FIX_193: Final[bool] = False
ROLLBACK_AUTHORITY_FIX_193: Final[bool] = False
RAILWAY_MUTATION_ENABLED_FIX_193: Final[bool] = False

PILOT_ARC_ROUTES_THROUGH_FIX_181_FIX_193: Final[bool] = True
ATLAS_TRADER_PILOT_ARC_ORCHESTRATOR_ORIGIN: Final[str] = (
    "mission_control_atlas_trader_pilot_arc_orchestrator"
)
ATLAS_TRADER_PILOT_ARC_ORCHESTRATOR_ROUTE_ID: Final[str] = (
    "mission_control_atlas_trader_pilot_arc_orchestrator"
)

ATLAS_TRADER_PILOT_ARC_ORCHESTRATOR_INVARIANT: Final[str] = (
    "atlas_trader_pilot_arc_orchestration_routes_through_fix_181_without_trust_granting_or_inherited_trust"
)

ATLAS_TRADER_PILOT_ARC_ORCHESTRATOR_RECORD_KINDS: Final[tuple[str, ...]] = (
    "repository_registration",
    "repo_issue_binding",
    "pilot_arc_trust_decision",
    "pilot_evidence_note",
    "pilot_arc_transition",
    "atlas_pilot_observation",
    "atlas_pilot_intervention",
    "pilot_arc_note",
)

ATLAS_TRADER_PILOT_ARC_ORCHESTRATOR_PRINCIPLES: Final[tuple[tuple[str, str], ...]] = (
    ("no_new_governance", "FIX 193 composes FIX 181–191 and FIX 260 — no new governance model."),
    ("pilot_arc_not_trust", "Pilot arc orchestration ≠ trust granting."),
    ("repository_scoped", "Evidence and trust are Atlas Trader scoped only."),
    ("no_inherited_trust", "AethOS and PilotOS UI trust do not transfer to Atlas Trader."),
    ("pilotos_prerequisite", "PilotOS UI trust baseline required before Atlas pilot 1."),
    ("fix_187_prerequisite", "FIX 187 Atlas expansion approval required before pilot 1."),
    ("sequential_pilots", "Pilot 1 → 2 → 3 follows independent evidence model."),
)

FORBIDDEN_PILOT_ARC_ACTIONS: Final[tuple[tuple[str, str], ...]] = (
    ("automatic_trust_grant", "Pilot completion never auto-grants CONDITIONALLY_TRUSTED."),
    ("trust_inheritance", "Atlas Trader never inherits AethOS or PilotOS UI trust."),
    ("hidden_pilot_run", "Pilots route through FIX 181 chat governance only."),
    ("gate_bypass", "Orchestrator never bypasses FIX 184/185/187 gates."),
    ("merge", "Orchestrator never merges pull requests."),
    ("deploy", "Orchestrator never deploys."),
    ("rollback", "Orchestrator never rollbacks."),
    ("railway_mutation", "Orchestrator never mutates Railway."),
    ("new_governance_layer", "Orchestrator does not introduce new governance authority."),
)

ATLAS_TRADER_PILOT_ARC_ORCHESTRATOR_EXECUTABLE: Final[bool] = True

MAX_ATLAS_TRADER_PILOT_ARC_ORCHESTRATOR_CONTENT_LEN: Final[int] = 4000
MAX_PERSISTED_ATLAS_TRADER_PILOT_ARC_ORCHESTRATOR_RECORDS: Final[int] = 500
