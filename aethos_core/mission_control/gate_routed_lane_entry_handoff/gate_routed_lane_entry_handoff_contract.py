# SPDX-License-Identifier: Apache-2.0
"""FIX 177 — gate-routed lane entry handoff contract (handoff ≠ lane entry execution)."""

from __future__ import annotations

from typing import Final

GATE_ROUTED_LANE_ENTRY_HANDOFF_SCHEMA_VERSION: Final[str] = (
    "mission_control_gate_routed_lane_entry_handoff_v1"
)
GATE_ROUTED_LANE_ENTRY_HANDOFF_RECORD_SCHEMA_VERSION: Final[str] = (
    "mission_control_gate_routed_lane_entry_handoff_record_v1"
)
GATE_ROUTED_LANE_ENTRY_HANDOFF_FIX: Final[str] = "FIX 177"

MUTATION_PERFORMED_FIX_177: Final[bool] = False
EXECUTION_PERFORMED_FIX_177: Final[bool] = False
LANE_ENTRY_EXECUTION_PERFORMED_FIX_177: Final[bool] = False
LANE_ADMISSION_EXECUTED_FIX_177: Final[bool] = False
AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_177: Final[bool] = False
AUTONOMOUS_EXECUTION_ENABLED_FIX_177: Final[bool] = False
AUTONOMOUS_LANE_ENTRY_ENABLED_FIX_177: Final[bool] = False
AUTONOMOUS_APPROVAL_ENABLED_FIX_177: Final[bool] = False
TIER_ESCALATION_ENABLED_FIX_177: Final[bool] = False
GATE_BYPASS_ENABLED_FIX_177: Final[bool] = False
CODE_WRITE_ENABLED_FIX_177: Final[bool] = False
PR_ACTION_ENABLED_FIX_177: Final[bool] = False
MERGE_DEPLOY_ENABLED_FIX_177: Final[bool] = False
RAILWAY_MUTATION_ENABLED_FIX_177: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_177: Final[bool] = False

GATE_ROUTED_LANE_ENTRY_HANDOFF_ROUTE_ID: Final[str] = (
    "mission_control_gate_routed_lane_entry_handoff"
)

GATE_ROUTED_LANE_ENTRY_HANDOFF_INVARIANT: Final[str] = (
    "gate_routed_lane_entry_handoff_converts_fix_176_human_decision_into_frozen_gate_handoff_packet_without_lane_entry_execution_or_gate_bypass"
)

HANDOFF_TIER: Final[str] = "tier_1_tier_2_bounded"

FROZEN_SOFTWARE_DELIVERY_GATES: Final[tuple[str, ...]] = (
    "issue_intake",
    "implementation_plan",
    "planning_approved",
    "patch_proposal_approved",
    "workspace_apply_approved",
    "workspace_verification",
    "github_preflight_approved",
    "software_delivery-stage",
)

# Section keys owned by FIX 176 — FIX 177 must never emit these (composition only).
UPSTREAM_SECTIONS_OWNED_BY_FIX_176: Final[tuple[str, ...]] = (
    "lane_readiness_board_upstream_read",
    "selected_lane_admission_decision",
    "decision_rationale",
    "accepted_risks_tradeoffs",
    "rejected_lane_candidates",
    "acknowledged_remaining_blockers",
    "lane_admission_decision_packet",
    "forbidden_decision_actions",
    "next_step_admission_decision_sequence",
    "decision_integrity_scoring",
)

GATE_ROUTED_LANE_ENTRY_HANDOFF_RECORD_KINDS: Final[tuple[str, ...]] = (
    "gate_handoff_artifact",
    "target_gate_note",
    "validation_requirement_note",
    "handoff_command_note",
    "forbidden_handoff_note",
    "gate_routed_lane_entry_handoff_record",
)

GATE_ROUTED_LANE_ENTRY_HANDOFF_PRINCIPLES: Final[tuple[tuple[str, str], ...]] = (
    ("composes_upstream", "FIX 177 composes FIX 176 human lane admission decision — never duplicates it."),
    ("handoff_not_execution", "Gate-routed handoff ≠ lane entry execution."),
    ("decision_required", "Handoff requires recorded human admit, hold, or reject from FIX 176."),
    ("frozen_gates_only", "Handoff routes to existing frozen gates — never around them."),
    ("rationale_included", "Decision rationale included in handoff packet."),
    ("risks_included", "Accepted risks and tradeoffs included in handoff packet."),
    ("blockers_included", "Remaining blockers included for gate validation."),
    ("gate_validates", "Frozen gate must still validate — handoff does not bypass."),
    ("no_lane_entry", "Handoff never autonomously enters governed lanes."),
    ("audit_replay_preserved", "Audit, replay, and receipt requirements are never reduced."),
)

FORBIDDEN_HANDOFF_ACTIONS: Final[tuple[tuple[str, str], ...]] = (
    ("lane_entry_execution", "Gate handoff never executes lane entry."),
    ("lane_admission_execution", "Gate handoff never performs lane admission."),
    ("approval_execution", "Gate handoff never executes approvals."),
    ("approval_bypass", "Gate handoff never bypasses existing approval gates."),
    ("gate_bypass", "Gate handoff never routes around frozen gates."),
    ("autonomous_handoff", "System never autonomously hands off to lanes."),
    ("code_write", "Gate handoff never writes code."),
    ("pr_action", "Gate handoff never performs PR actions."),
    ("merge_deploy", "Gate handoff never merges or deploys."),
    ("railway_mutation", "Gate handoff never mutates Railway infrastructure."),
    ("decision_recompute", "Gate handoff never redefines FIX 176 decision sections."),
)

GATE_ROUTED_LANE_ENTRY_HANDOFF_EXECUTABLE: Final[bool] = False

MAX_GATE_ROUTED_LANE_ENTRY_HANDOFF_CONTENT_LEN: Final[int] = 4000
MAX_PERSISTED_GATE_ROUTED_LANE_ENTRY_HANDOFF_RECORDS: Final[int] = 500
