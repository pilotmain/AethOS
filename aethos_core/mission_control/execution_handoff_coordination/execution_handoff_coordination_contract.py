# SPDX-License-Identifier: Apache-2.0
"""FIX 167 — governed execution handoff coordination contract."""

from __future__ import annotations

from typing import Final

EXECUTION_HANDOFF_COORDINATION_SCHEMA_VERSION: Final[str] = "mission_control_execution_handoff_coordination_v1"
EXECUTION_HANDOFF_COORDINATION_RECORD_SCHEMA_VERSION: Final[str] = (
    "mission_control_execution_handoff_coordination_record_v1"
)
EXECUTION_HANDOFF_COORDINATION_FIX: Final[str] = "FIX 167"

MUTATION_PERFORMED_FIX_167: Final[bool] = False
AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_167: Final[bool] = False
AUTONOMOUS_EXECUTION_ENABLED_FIX_167: Final[bool] = False
AUTONOMOUS_APPROVAL_ENABLED_FIX_167: Final[bool] = False
AUTONOMOUS_LANE_ENTRY_ENABLED_FIX_167: Final[bool] = False
PR_OPEN_ENABLED_FIX_167: Final[bool] = False
MERGE_DEPLOY_ENABLED_FIX_167: Final[bool] = False
RAILWAY_MUTATION_ENABLED_FIX_167: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_167: Final[bool] = False

EXECUTION_HANDOFF_COORDINATION_ROUTE_ID: Final[str] = "mission_control_execution_handoff_coordination"

EXECUTION_HANDOFF_COORDINATION_INVARIANT: Final[str] = (
    "execution_handoff_coordination_connects_human_decision_to_governed_lanes_recommendation_only_no_execution_authority"
)

HANDOFF_RECORD_KINDS: Final[tuple[str, ...]] = (
    "handoff_artifact",
    "lane_gate_note",
    "approval_requirement_note",
    "blocker_note",
    "forbidden_action_note",
    "next_step_note",
    "handoff_coordination_record",
)

HANDOFF_PRINCIPLES: Final[tuple[tuple[str, str], ...]] = (
    ("handoff_coordinates_not_executes", "Handoff connects human decision to lanes; never executes autonomously."),
    ("decision_required_before_handoff", "Recorded human selection is required before lane handoff coordination."),
    ("lanes_mapped_not_entered", "Eligible lanes are mapped; handoff never enters lanes autonomously."),
    ("gates_listed_not_passed", "Required lane gates are listed; handoff never passes gates."),
    ("approvals_listed_not_granted", "Required approvals are listed; handoff never grants them."),
    ("blockers_surfaced_not_bypassed", "Remaining blockers are surfaced; handoff does not bypass governance."),
    ("forbidden_actions_explicit", "Forbidden actions remain explicit at handoff boundary."),
    ("next_steps_advisory", "Next-step command sequence is advisory for operator use only."),
)

PATH_LANE_MAP: Final[tuple[tuple[str, tuple[str, ...]], ...]] = (
    ("constitutional_review_path", ("software_delivery", "route_diagnostics")),
    ("evidence_gathering_path", ("route_diagnostics", "durable_jobs")),
    ("governed_delivery_continuation", ("software_delivery", "multi_agent_collaboration")),
    ("hold_no_go_path", ()),
)

FORBIDDEN_HANDOFF_ACTIONS: Final[tuple[tuple[str, str], ...]] = (
    ("autonomous_execution", "Handoff coordination never executes lane actions."),
    ("autonomous_approval", "Handoff coordination never approves gates or inbox items."),
    ("autonomous_lane_entry", "Handoff coordination never enters execution lanes autonomously."),
    ("pr_open", "Handoff coordination never opens PRs."),
    ("merge_deploy", "Handoff coordination never merges or deploys."),
    ("railway_mutation", "Handoff coordination never mutates Railway infrastructure."),
)

LANE_NEXT_STEP_HINTS: Final[tuple[tuple[str, str], ...]] = (
    ("software_delivery", "Review software delivery loop status and next governed stage"),
    ("route_diagnostics", "Review cross-lane snapshot and evidence bundle"),
    ("durable_jobs", "Review job replay and rerun plan"),
    ("multi_agent_collaboration", "Review bounded agent collaboration status (FIX 127)"),
    ("railway_orchestration", "Review Railway lane with explicit approval phrases only"),
)

HANDOFF_RECOMMENDATION_EXECUTABLE: Final[bool] = False

MAX_HANDOFF_CONTENT_LEN: Final[int] = 4000
MAX_PERSISTED_HANDOFF_RECORDS: Final[int] = 500
