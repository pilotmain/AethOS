# SPDX-License-Identifier: Apache-2.0
"""FIX 171 — bounded execution participation contract (envelope-scoped agent coordination)."""

from __future__ import annotations

from typing import Final

BOUNDED_EXECUTION_PARTICIPATION_SCHEMA_VERSION: Final[str] = (
    "mission_control_bounded_execution_participation_v1"
)
BOUNDED_EXECUTION_PARTICIPATION_RECORD_SCHEMA_VERSION: Final[str] = (
    "mission_control_bounded_execution_participation_record_v1"
)
BOUNDED_EXECUTION_PARTICIPATION_FIX: Final[str] = "FIX 171"

MUTATION_PERFORMED_FIX_171: Final[bool] = False
AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_171: Final[bool] = False
AUTONOMOUS_EXECUTION_ENABLED_FIX_171: Final[bool] = False
AUTONOMOUS_LANE_ENTRY_ENABLED_FIX_171: Final[bool] = False
AUTONOMOUS_APPROVAL_ENABLED_FIX_171: Final[bool] = False
TIER_ESCALATION_ENABLED_FIX_171: Final[bool] = False
GATE_BYPASS_ENABLED_FIX_171: Final[bool] = False
PR_OPEN_ENABLED_FIX_171: Final[bool] = False
MERGE_DEPLOY_ENABLED_FIX_171: Final[bool] = False
RAILWAY_MUTATION_ENABLED_FIX_171: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_171: Final[bool] = False

BOUNDED_EXECUTION_PARTICIPATION_ROUTE_ID: Final[str] = "mission_control_bounded_execution_participation"

BOUNDED_EXECUTION_PARTICIPATION_INVARIANT: Final[str] = (
    "bounded_execution_participation_coordinates_agent_work_within_authorized_tier_1_2_envelope_without_autonomous_lane_entry_or_gate_bypass"
)

PARTICIPATION_TIER: Final[str] = "tier_1_tier_2_bounded"

FORBIDDEN_PARTICIPATION_LANES: Final[tuple[str, ...]] = (
    "railway_orchestration",
    "production_governance",
)

ALLOWED_PARTICIPATION_LANES: Final[tuple[str, ...]] = (
    "software_delivery",
    "multi_agent_collaboration",
    "route_diagnostics",
    "durable_jobs",
)

BOUNDED_EXECUTION_PARTICIPATION_RECORD_KINDS: Final[tuple[str, ...]] = (
    "participation_artifact",
    "agent_scope_note",
    "gate_routed_action_note",
    "reengagement_note",
    "forbidden_participation_note",
    "bounded_execution_participation_record",
)

BOUNDED_EXECUTION_PARTICIPATION_PRINCIPLES: Final[tuple[tuple[str, str], ...]] = (
    ("envelope_required", "Participation requires a valid FIX 170 mission authorization envelope."),
    ("participation_not_authority", "Agent participation coordinates work — it does not grant execution authority."),
    ("no_autonomous_lane_entry", "Agents never autonomously enter governed lanes."),
    ("gates_remain_enforced", "Every action routes through existing gate checks — no approval bypass."),
    ("no_tier_escalation", "Tier 1–2 participation never satisfies Tier 3–4 requirements."),
    ("no_railway_production", "Software delivery envelope never includes Railway or production participation."),
    ("no_merge_deploy", "Participation never includes merge or deploy authority."),
    ("reengagement_on_escalation", "Human re-engagement required only on escalation triggers."),
    ("audit_replay_preserved", "Audit, replay, and receipt requirements are never reduced."),
)

FORBIDDEN_PARTICIPATION_ACTIONS: Final[tuple[tuple[str, str], ...]] = (
    ("autonomous_lane_entry", "Agents never autonomously enter governed lanes."),
    ("tier_3_4_action", "Participation never performs Tier 3–4 actions."),
    ("railway_participation", "Participation never includes Railway orchestration."),
    ("production_participation", "Participation never includes production governance."),
    ("merge_deploy", "Participation never includes merge or deploy authority."),
    ("approval_bypass", "Participation never bypasses existing approval gates."),
    ("envelope_expansion", "Participation never expands beyond authorized envelope."),
    ("autonomous_execution", "Participation never grants autonomous execution authority."),
)

BOUNDED_EXECUTION_PARTICIPATION_EXECUTABLE: Final[bool] = False

MAX_BOUNDED_EXECUTION_PARTICIPATION_CONTENT_LEN: Final[int] = 4000
MAX_PERSISTED_BOUNDED_EXECUTION_PARTICIPATION_RECORDS: Final[int] = 500
