# SPDX-License-Identifier: Apache-2.0
"""FIX 195 — Nexora pilot arc orchestrator contract."""

from __future__ import annotations

from typing import Final

NEXORA_PILOT_ARC_ORCHESTRATOR_SCHEMA_VERSION: Final[str] = (
    "mission_control_nexora_pilot_arc_orchestrator_v1"
)
NEXORA_PILOT_ARC_ORCHESTRATOR_RECORD_SCHEMA_VERSION: Final[str] = (
    "mission_control_nexora_pilot_arc_orchestrator_record_v1"
)
NEXORA_PILOT_ARC_ORCHESTRATOR_FIX: Final[str] = "FIX 195"

NEXORA_REPOSITORY: Final[str] = "pilotmain/nexora-monorepo-starter"
NEXORA_DEFAULT_REPO_ISSUE: Final[str] = "pilotmain/nexora-monorepo-starter#1"

NEXORA_PILOT_SESSIONS: Final[tuple[str, ...]] = (
    "nexora-pilot-1",
    "nexora-pilot-2",
    "nexora-pilot-3",
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

MUTATION_PERFORMED_FIX_195: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_195: Final[bool] = False
TRUST_GRANTING_AUTHORITY_FIX_195: Final[bool] = False
TRUST_INHERITANCE_ENABLED_FIX_195: Final[bool] = False
CROSS_REPO_AUTHORITY_FIX_195: Final[bool] = False
PILOT_EXECUTION_BYPASS_ENABLED_FIX_195: Final[bool] = False
HIDDEN_PILOT_EXECUTION_ENABLED_FIX_195: Final[bool] = False
GATE_BYPASS_ENABLED_FIX_195: Final[bool] = False
MERGE_AUTHORITY_FIX_195: Final[bool] = False
DEPLOY_AUTHORITY_FIX_195: Final[bool] = False
ROLLBACK_AUTHORITY_FIX_195: Final[bool] = False
PROVIDER_AUTHORITY_FIX_195: Final[bool] = False
RAILWAY_MUTATION_ENABLED_FIX_195: Final[bool] = False

PILOT_ARC_ROUTES_THROUGH_FIX_181_FIX_195: Final[bool] = True
NEXORA_PILOT_ARC_ORCHESTRATOR_ORIGIN: Final[str] = "mission_control_nexora_pilot_arc_orchestrator"
NEXORA_PILOT_ARC_ORCHESTRATOR_ROUTE_ID: Final[str] = "mission_control_nexora_pilot_arc_orchestrator"

NEXORA_PILOT_ARC_ORCHESTRATOR_INVARIANT: Final[str] = (
    "nexora_pilot_arc_orchestration_routes_through_fix_181_without_trust_granting_or_inherited_trust"
)

NEXORA_PILOT_ARC_ORCHESTRATOR_RECORD_KINDS: Final[tuple[str, ...]] = (
    "repository_registration",
    "repo_issue_binding",
    "pilot_arc_trust_decision",
    "pilot_evidence_note",
    "pilot_arc_transition",
    "nexora_pilot_observation",
    "nexora_pilot_intervention",
    "pilot_arc_note",
)

NEXORA_PILOT_ARC_ORCHESTRATOR_PRINCIPLES: Final[tuple[tuple[str, str], ...]] = (
    ("no_new_governance", "FIX 195 composes FIX 181–191 and FIX 260 — no new governance model."),
    ("pilot_arc_not_trust", "Pilot arc orchestration ≠ trust granting."),
    ("repository_scoped", "Evidence and trust are Nexora scoped only."),
    ("no_inherited_trust", "AethOS, PilotOS UI, and Atlas Trader trust do not transfer to Nexora."),
    ("multi_repo_prerequisites", "FIX 186/192/194 trust baselines required before Nexora pilot 1."),
    ("fix_187_prerequisite", "FIX 187 Nexora expansion approval required before pilot 1."),
    ("sequential_pilots", "Pilot 1 → 2 → 3 follows independent evidence model."),
)

FORBIDDEN_PILOT_ARC_ACTIONS: Final[tuple[tuple[str, str], ...]] = (
    ("automatic_trust_grant", "Pilot completion never auto-grants CONDITIONALLY_TRUSTED."),
    ("trust_inheritance", "Nexora never inherits trust from other repositories."),
    ("hidden_pilot_run", "Pilots route through FIX 181 chat governance only."),
    ("gate_bypass", "Orchestrator never bypasses FIX 184/185/187 gates."),
    ("merge", "Orchestrator never merges pull requests."),
    ("deploy", "Orchestrator never deploys."),
    ("rollback", "Orchestrator never rollbacks."),
    ("provider_mutation", "Orchestrator never mutates providers."),
    ("railway_mutation", "Orchestrator never mutates Railway."),
    ("new_governance_layer", "Orchestrator does not introduce new governance authority."),
)

NEXORA_PILOT_ARC_ORCHESTRATOR_EXECUTABLE: Final[bool] = True

MAX_NEXORA_PILOT_ARC_ORCHESTRATOR_CONTENT_LEN: Final[int] = 4000
MAX_PERSISTED_NEXORA_PILOT_ARC_ORCHESTRATOR_RECORDS: Final[int] = 500
