# SPDX-License-Identifier: Apache-2.0
"""FIX 170 — mission authorization contract (bounded envelope under governance friction)."""

from __future__ import annotations

from typing import Final

MISSION_AUTHORIZATION_SCHEMA_VERSION: Final[str] = "mission_control_mission_authorization_v1"
MISSION_AUTHORIZATION_RECORD_SCHEMA_VERSION: Final[str] = "mission_control_mission_authorization_record_v1"
MISSION_AUTHORIZATION_FIX: Final[str] = "FIX 170"

MUTATION_PERFORMED_FIX_170: Final[bool] = False
AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_170: Final[bool] = False
AUTONOMOUS_EXECUTION_ENABLED_FIX_170: Final[bool] = False
AUTONOMOUS_APPROVAL_ENABLED_FIX_170: Final[bool] = False
AUTONOMOUS_LANE_EXPANSION_ENABLED_FIX_170: Final[bool] = False
TIER_ESCALATION_ENABLED_FIX_170: Final[bool] = False
GATE_BYPASS_ENABLED_FIX_170: Final[bool] = False
PR_OPEN_ENABLED_FIX_170: Final[bool] = False
MERGE_DEPLOY_ENABLED_FIX_170: Final[bool] = False
RAILWAY_MUTATION_ENABLED_FIX_170: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_170: Final[bool] = False

MISSION_AUTHORIZATION_ROUTE_ID: Final[str] = "mission_control_mission_authorization"

MISSION_AUTHORIZATION_INVARIANT: Final[str] = (
    "mission_authorization_grants_bounded_tier_1_2_work_envelope_without_bypassing_existing_gates_or_expanding_authority"
)

AUTHORIZATION_TIER: Final[str] = "tier_1_tier_2_bounded"

FORBIDDEN_IMPLICIT_LANES: Final[tuple[str, ...]] = (
    "railway_orchestration",
    "production_governance",
)

PATH_ENVELOPE_MAP: Final[tuple[tuple[str, tuple[str, ...], str], ...]] = (
    ("governed_delivery_continuation", ("software_delivery", "multi_agent_collaboration"), "tier_1_tier_2_bounded"),
    ("constitutional_review_path", ("software_delivery", "route_diagnostics"), "tier_1_tier_2_bounded"),
    ("evidence_gathering_path", ("route_diagnostics", "durable_jobs"), "tier_0_tier_1_bounded"),
    ("hold_no_go_path", (), "no_authorization"),
)

MISSION_AUTHORIZATION_RECORD_KINDS: Final[tuple[str, ...]] = (
    "mission_authorization_artifact",
    "envelope_scope_note",
    "gate_check_note",
    "reengagement_note",
    "forbidden_auth_note",
    "mission_authorization_record",
)

MISSION_AUTHORIZATION_PRINCIPLES: Final[tuple[tuple[str, str], ...]] = (
    ("envelope_not_permission", "Authorization is a bounded envelope — not permission to do anything."),
    ("gates_remain_enforced", "Existing frozen gates remain enforced; authorization does not bypass them."),
    ("no_silent_lane_expansion", "Allowed lanes cannot silently expand to Railway or production."),
    ("no_tier_escalation", "Tier 1–2 authorization never satisfies Tier 3–4 requirements."),
    ("reengagement_on_escalation", "Human re-engagement only when risk, scope, or tier escalates."),
    ("audit_replay_preserved", "Audit, replay, and receipt requirements are never reduced."),
    ("human_decision_required", "Mission authorization requires FIX 166 human decision context."),
    ("governance_friction_additive", "Authorization reduces repetition — never reduces governance."),
)

FORBIDDEN_AUTHORIZATION_ACTIONS: Final[tuple[tuple[str, str], ...]] = (
    ("silent_lane_expansion", "Authorization never silently expands allowed lanes."),
    ("blast_radius_expansion", "Authorization never expands blast radius beyond granted envelope."),
    ("tier_escalation", "Tier 1–2 authorization never satisfies Tier 3–4 approval requirements."),
    ("railway_from_delivery_auth", "Software delivery authorization never includes Railway or production."),
    ("gate_bypass", "Authorization never bypasses frozen software delivery or infra gates."),
    ("audit_reduction", "Authorization never reduces audit, replay, or receipt requirements."),
    ("autonomous_execution", "Mission authorization never grants autonomous execution authority."),
)

MISSION_AUTHORIZATION_EXECUTABLE: Final[bool] = False

MAX_MISSION_AUTHORIZATION_CONTENT_LEN: Final[int] = 4000
MAX_PERSISTED_MISSION_AUTHORIZATION_RECORDS: Final[int] = 500
