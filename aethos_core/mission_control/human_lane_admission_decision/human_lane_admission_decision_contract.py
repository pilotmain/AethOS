# SPDX-License-Identifier: Apache-2.0
"""FIX 176 — human lane admission decision contract (decision ≠ lane entry execution)."""

from __future__ import annotations

from typing import Final

HUMAN_LANE_ADMISSION_DECISION_SCHEMA_VERSION: Final[str] = (
    "mission_control_human_lane_admission_decision_v1"
)
HUMAN_LANE_ADMISSION_DECISION_RECORD_SCHEMA_VERSION: Final[str] = (
    "mission_control_human_lane_admission_decision_record_v1"
)
HUMAN_LANE_ADMISSION_DECISION_FIX: Final[str] = "FIX 176"

MUTATION_PERFORMED_FIX_176: Final[bool] = False
EXECUTION_PERFORMED_FIX_176: Final[bool] = False
LANE_ENTRY_EXECUTION_PERFORMED_FIX_176: Final[bool] = False
LANE_ADMISSION_EXECUTED_FIX_176: Final[bool] = False
AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_176: Final[bool] = False
AUTONOMOUS_EXECUTION_ENABLED_FIX_176: Final[bool] = False
AUTONOMOUS_LANE_ENTRY_ENABLED_FIX_176: Final[bool] = False
AUTONOMOUS_APPROVAL_ENABLED_FIX_176: Final[bool] = False
TIER_ESCALATION_ENABLED_FIX_176: Final[bool] = False
GATE_BYPASS_ENABLED_FIX_176: Final[bool] = False
CODE_WRITE_ENABLED_FIX_176: Final[bool] = False
PR_ACTION_ENABLED_FIX_176: Final[bool] = False
MERGE_DEPLOY_ENABLED_FIX_176: Final[bool] = False
RAILWAY_MUTATION_ENABLED_FIX_176: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_176: Final[bool] = False

HUMAN_LANE_ADMISSION_DECISION_ROUTE_ID: Final[str] = (
    "mission_control_human_lane_admission_decision"
)

HUMAN_LANE_ADMISSION_DECISION_INVARIANT: Final[str] = (
    "human_lane_admission_decision_records_human_admit_hold_or_reject_after_fix_175_board_review_without_lane_entry_execution_or_gate_bypass"
)

DECISION_TIER: Final[str] = "tier_1_tier_2_bounded"

LANE_ADMISSION_DECISION_VALUES: Final[tuple[str, ...]] = (
    "admit",
    "hold",
    "reject",
)

# Section keys owned by FIX 175 — FIX 176 must never emit these (composition only).
UPSTREAM_SECTIONS_OWNED_BY_FIX_175: Final[tuple[str, ...]] = (
    "lane_recommendation_upstream_read",
    "authorization_envelope_status",
    "recommended_lane_candidates_board",
    "blocked_lanes_board",
    "required_gates_board",
    "missing_prerequisites_board",
    "escalation_requirements_board",
    "risk_blast_radius_summary",
    "lane_readiness_board_packet",
    "forbidden_board_actions",
    "next_step_lane_readiness_board_sequence",
    "lane_readiness_board_integrity_scoring",
)

HUMAN_LANE_ADMISSION_DECISION_RECORD_KINDS: Final[tuple[str, ...]] = (
    "lane_admission_decision_record",
    "decision_rationale_note",
    "risk_tradeoff_acceptance_note",
    "rejected_candidate_note",
    "acknowledged_blocker_note",
    "lane_admission_decision_artifact",
    "human_lane_admission_decision_record",
)

HUMAN_LANE_ADMISSION_DECISION_PRINCIPLES: Final[tuple[tuple[str, str], ...]] = (
    ("composes_upstream", "FIX 176 composes FIX 175 lane readiness board — never duplicates it."),
    ("human_decides_not_system", "Only humans record admit, hold, or reject — never autonomous."),
    ("decision_not_execution", "Human lane admission decision ≠ lane entry execution."),
    ("board_required", "Decision requires FIX 175 lane readiness board context."),
    ("rationale_recorded", "Decision rationale is a first-class traceable artifact."),
    ("risks_consciously_accepted", "Accepted risks and tradeoffs recorded at decision time."),
    ("rejections_visible", "Rejected lane candidates captured alongside selected decision."),
    ("blockers_acknowledged", "Remaining blockers acknowledged by human at decision time."),
    ("no_lane_entry", "Decision records choice — FIX 177 performs gate-routed handoff only."),
    ("audit_replay_preserved", "Audit, replay, and receipt requirements are never reduced."),
)

FORBIDDEN_DECISION_ACTIONS: Final[tuple[tuple[str, str], ...]] = (
    ("lane_entry_execution", "Human lane admission decision never executes lane entry."),
    ("lane_admission_execution", "Human lane admission decision never performs lane admission."),
    ("approval_execution", "Human lane admission decision never executes approvals."),
    ("approval_bypass", "Human lane admission decision never bypasses existing approval gates."),
    ("autonomous_decision", "System never autonomously admits, holds, or rejects lane entry."),
    ("code_write", "Human lane admission decision never writes code."),
    ("pr_action", "Human lane admission decision never performs PR actions."),
    ("merge_deploy", "Human lane admission decision never merges or deploys."),
    ("railway_mutation", "Human lane admission decision never mutates Railway infrastructure."),
    ("gate_bypass", "Human lane admission decision never routes around frozen gates."),
    ("board_recompute", "Human lane admission decision never redefines FIX 175 board sections."),
)

HUMAN_LANE_ADMISSION_DECISION_EXECUTABLE: Final[bool] = False

MAX_HUMAN_LANE_ADMISSION_DECISION_CONTENT_LEN: Final[int] = 4000
MAX_PERSISTED_HUMAN_LANE_ADMISSION_DECISION_RECORDS: Final[int] = 500
