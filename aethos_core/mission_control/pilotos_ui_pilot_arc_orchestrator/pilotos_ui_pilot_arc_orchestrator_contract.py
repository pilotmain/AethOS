# SPDX-License-Identifier: Apache-2.0
"""FIX 188 — PilotOS UI pilot arc orchestrator contract."""

from __future__ import annotations

from typing import Final

PILOTOS_UI_PILOT_ARC_ORCHESTRATOR_SCHEMA_VERSION: Final[str] = (
    "mission_control_pilotos_ui_pilot_arc_orchestrator_v1"
)
PILOTOS_UI_PILOT_ARC_ORCHESTRATOR_RECORD_SCHEMA_VERSION: Final[str] = (
    "mission_control_pilotos_ui_pilot_arc_orchestrator_record_v1"
)
PILOTOS_UI_PILOT_ARC_ORCHESTRATOR_FIX: Final[str] = "FIX 188"

PILOTOS_UI_REPOSITORY: Final[str] = "pilotmain/pilot-os-ui"
PILOTOS_UI_DEFAULT_REPO_ISSUE: Final[str] = "pilotmain/pilot-os-ui#1"

PILOTOS_PILOT_SESSIONS: Final[tuple[str, ...]] = (
    "pilotos-pilot-1",
    "pilotos-pilot-2",
    "pilotos-pilot-3",
)

PILOT_ARC_STATES: Final[tuple[str, ...]] = (
    "UNPROVEN",
    "PILOT_1_RUNNING",
    "PILOT_1_COMPLETE",
    "PILOT_2_RUNNING",
    "PILOT_2_COMPLETE",
    "PILOT_3_RUNNING",
    "PILOT_3_COMPLETE",
    "TRUST_REVIEW_PENDING",
    "CONDITIONALLY_TRUSTED",
)

MUTATION_PERFORMED_FIX_188: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_188: Final[bool] = False
AUTOMATIC_TRUST_GRANTING_ENABLED_FIX_188: Final[bool] = False
TRUST_TRANSFER_ENABLED_FIX_188: Final[bool] = False
HIDDEN_PILOT_EXECUTION_ENABLED_FIX_188: Final[bool] = False
GATE_BYPASS_ENABLED_FIX_188: Final[bool] = False
MERGE_ENABLED_FIX_188: Final[bool] = False
DEPLOY_ENABLED_FIX_188: Final[bool] = False
RAILWAY_MUTATION_ENABLED_FIX_188: Final[bool] = False

PILOT_ARC_ROUTES_THROUGH_FIX_181_FIX_188: Final[bool] = True
PILOTOS_UI_PILOT_ARC_ORCHESTRATOR_ORIGIN: Final[str] = (
    "mission_control_pilotos_ui_pilot_arc_orchestrator"
)
PILOTOS_UI_PILOT_ARC_ORCHESTRATOR_ROUTE_ID: Final[str] = (
    "mission_control_pilotos_ui_pilot_arc_orchestrator"
)

PILOTOS_UI_PILOT_ARC_ORCHESTRATOR_INVARIANT: Final[str] = (
    "pilotos_ui_pilot_arc_orchestration_routes_through_fix_181_without_automatic_trust_granting_or_inherited_trust"
)

PILOTOS_UI_PILOT_ARC_ORCHESTRATOR_RECORD_KINDS: Final[tuple[str, ...]] = (
    "repository_registration",
    "repo_issue_binding",
    "pilot_arc_trust_decision",
    "pilot_evidence_note",
    "pilot_arc_transition",
)

PILOTOS_UI_PILOT_ARC_ORCHESTRATOR_PRINCIPLES: Final[tuple[tuple[str, str], ...]] = (
    ("no_new_governance", "FIX 188 composes FIX 181–187 — no new governance model."),
    ("pilot_arc_not_trust", "Pilot arc orchestration ≠ trust granting."),
    ("human_trust_review", "Operator records trust decision after evidence review."),
    ("repository_scoped", "Evidence and trust are PilotOS UI scoped only."),
    ("no_inherited_trust", "AethOS trust does not transfer to PilotOS UI."),
    ("sequential_pilots", "Pilot 1 → 2 → 3 follows AethOS evidence model."),
    ("fix_187_prerequisite", "FIX 187 expansion approval required before pilot 1."),
)

FORBIDDEN_PILOT_ARC_ACTIONS: Final[tuple[tuple[str, str], ...]] = (
    ("automatic_trust_grant", "Pilot completion never auto-grants CONDITIONALLY_TRUSTED."),
    ("trust_transfer", "PilotOS UI never inherits AethOS trust."),
    ("hidden_pilot_run", "Pilots route through FIX 181 chat governance only."),
    ("gate_bypass", "Orchestrator never bypasses FIX 184/185/187 gates."),
    ("merge", "Orchestrator never merges pull requests."),
    ("deploy", "Orchestrator never deploys."),
    ("railway_mutation", "Orchestrator never mutates Railway."),
    ("new_governance_layer", "Orchestrator does not introduce new governance authority."),
)

PILOTOS_UI_PILOT_ARC_ORCHESTRATOR_EXECUTABLE: Final[bool] = True

MAX_PILOTOS_UI_PILOT_ARC_ORCHESTRATOR_CONTENT_LEN: Final[int] = 4000
MAX_PERSISTED_PILOTOS_UI_PILOT_ARC_ORCHESTRATOR_RECORDS: Final[int] = 500
