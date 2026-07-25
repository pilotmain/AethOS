# SPDX-License-Identifier: Apache-2.0
"""FIX 172 — governed task execution coordination contract (coordinate without executing)."""

from __future__ import annotations

from typing import Final

GOVERNED_TASK_EXECUTION_COORDINATION_SCHEMA_VERSION: Final[str] = (
    "mission_control_governed_task_execution_coordination_v1"
)
GOVERNED_TASK_EXECUTION_COORDINATION_RECORD_SCHEMA_VERSION: Final[str] = (
    "mission_control_governed_task_execution_coordination_record_v1"
)
GOVERNED_TASK_EXECUTION_COORDINATION_FIX: Final[str] = "FIX 172"

MUTATION_PERFORMED_FIX_172: Final[bool] = False
EXECUTION_PERFORMED_FIX_172: Final[bool] = False
AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_172: Final[bool] = False
AUTONOMOUS_EXECUTION_ENABLED_FIX_172: Final[bool] = False
AUTONOMOUS_LANE_ENTRY_ENABLED_FIX_172: Final[bool] = False
AUTONOMOUS_APPROVAL_ENABLED_FIX_172: Final[bool] = False
TIER_ESCALATION_ENABLED_FIX_172: Final[bool] = False
GATE_BYPASS_ENABLED_FIX_172: Final[bool] = False
CODE_WRITE_ENABLED_FIX_172: Final[bool] = False
PR_ACTION_ENABLED_FIX_172: Final[bool] = False
MERGE_DEPLOY_ENABLED_FIX_172: Final[bool] = False
RAILWAY_MUTATION_ENABLED_FIX_172: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_172: Final[bool] = False

GOVERNED_TASK_EXECUTION_COORDINATION_ROUTE_ID: Final[str] = (
    "mission_control_governed_task_execution_coordination"
)

GOVERNED_TASK_EXECUTION_COORDINATION_INVARIANT: Final[str] = (
    "governed_task_execution_coordination_assigns_and_tracks_bounded_packages_without_performing_execution_or_bypassing_gates"
)

COORDINATION_TIER: Final[str] = "tier_1_tier_2_bounded"

PACKAGE_DEPENDENCY_ORDER: Final[tuple[tuple[str, tuple[str, ...]], ...]] = (
    ("planner_agent", ()),
    ("risk_agent", ("planner_agent",)),
    ("verification_agent", ("risk_agent",)),
    ("diff_audit_agent", ("verification_agent",)),
    ("delivery_agent", ("verification_agent",)),
)

PACKAGE_LIFECYCLE_STATES: Final[tuple[str, ...]] = (
    "pending",
    "ready",
    "coordinating",
    "gate_routed",
    "blocked",
)

GOVERNED_TASK_EXECUTION_COORDINATION_RECORD_KINDS: Final[tuple[str, ...]] = (
    "coordination_artifact",
    "package_assignment_note",
    "lifecycle_note",
    "dependency_note",
    "escalation_note",
    "forbidden_coordination_note",
    "governed_task_execution_coordination_record",
)

GOVERNED_TASK_EXECUTION_COORDINATION_PRINCIPLES: Final[tuple[tuple[str, str], ...]] = (
    ("participation_required", "Coordination requires FIX 171 bounded execution participation context."),
    ("coordination_not_execution", "Execution coordination assigns and tracks — it never performs execution."),
    ("agents_assigned_not_authorized", "Work packages assign to bounded agents without execution authority."),
    ("lifecycle_read_only", "Package lifecycle tracking is coordination cognition — not lane execution."),
    ("dependencies_sequenced_not_bypassed", "Dependencies and sequencing route through existing gates."),
    ("parallel_readiness_coordinated", "Parallel package readiness is coordinated without gate bypass."),
    ("escalation_monitored", "Escalation conditions trigger human re-engagement — never autonomous expansion."),
    ("outcomes_gate_routed", "Package outcomes route to existing gates — coordination is not gate bypass."),
    ("audit_replay_preserved", "Audit, replay, and receipt requirements are never reduced."),
)

FORBIDDEN_COORDINATION_ACTIONS: Final[tuple[tuple[str, str], ...]] = (
    ("code_write_outside_lane", "Coordination never writes code outside existing governed lanes."),
    ("pr_action_outside_lane", "Coordination never performs PR actions outside existing governed lanes."),
    ("merge_deploy", "Coordination never merges or deploys."),
    ("railway_mutation", "Coordination never mutates Railway infrastructure."),
    ("gate_bypass", "Coordination never bypasses existing approval gates."),
    ("autonomous_lane_entry", "Coordination never autonomously enters governed lanes."),
    ("execution_authority", "Coordination never grants execution authority."),
    ("autonomous_execution", "Coordination never performs autonomous execution."),
)

GOVERNED_TASK_EXECUTION_COORDINATION_EXECUTABLE: Final[bool] = False

MAX_GOVERNED_TASK_EXECUTION_COORDINATION_CONTENT_LEN: Final[int] = 4000
MAX_PERSISTED_GOVERNED_TASK_EXECUTION_COORDINATION_RECORDS: Final[int] = 500
