# SPDX-License-Identifier: Apache-2.0
"""FIX 175 — governed lane readiness board contract (board ≠ admission decision)."""

from __future__ import annotations

from typing import Final

GOVERNED_LANE_READINESS_BOARD_SCHEMA_VERSION: Final[str] = (
    "mission_control_governed_lane_readiness_board_v1"
)
GOVERNED_LANE_READINESS_BOARD_RECORD_SCHEMA_VERSION: Final[str] = (
    "mission_control_governed_lane_readiness_board_record_v1"
)
GOVERNED_LANE_READINESS_BOARD_FIX: Final[str] = "FIX 175"

MUTATION_PERFORMED_FIX_175: Final[bool] = False
EXECUTION_PERFORMED_FIX_175: Final[bool] = False
LANE_ADMISSION_DECISION_PERFORMED_FIX_175: Final[bool] = False
LANE_ADMISSION_PERFORMED_FIX_175: Final[bool] = False
AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_175: Final[bool] = False
AUTONOMOUS_EXECUTION_ENABLED_FIX_175: Final[bool] = False
AUTONOMOUS_LANE_ENTRY_ENABLED_FIX_175: Final[bool] = False
AUTONOMOUS_APPROVAL_ENABLED_FIX_175: Final[bool] = False
TIER_ESCALATION_ENABLED_FIX_175: Final[bool] = False
GATE_BYPASS_ENABLED_FIX_175: Final[bool] = False
CODE_WRITE_ENABLED_FIX_175: Final[bool] = False
PR_ACTION_ENABLED_FIX_175: Final[bool] = False
MERGE_DEPLOY_ENABLED_FIX_175: Final[bool] = False
RAILWAY_MUTATION_ENABLED_FIX_175: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_175: Final[bool] = False

GOVERNED_LANE_READINESS_BOARD_ROUTE_ID: Final[str] = (
    "mission_control_governed_lane_readiness_board"
)

GOVERNED_LANE_READINESS_BOARD_INVARIANT: Final[str] = (
    "governed_lane_readiness_board_consolidates_fix_174_lane_recommendation_for_human_review_without_lane_admission_decision_or_execution_authority"
)

BOARD_TIER: Final[str] = "tier_1_tier_2_bounded"

# Section keys owned by FIX 174 — FIX 175 must never emit these (composition only).
UPSTREAM_SECTIONS_OWNED_BY_FIX_174: Final[tuple[str, ...]] = (
    "readiness_upstream_read",
    "gate_review_upstream_read",
    "lane_entry_candidates",
    "eligibility_rationale",
    "blocked_lane_explanations",
    "missing_prerequisites_references",
    "escalation_requirements",
    "recommended_next_gate",
    "forbidden_lane_recommendation_actions",
    "next_step_lane_recommendation_sequence",
    "lane_recommendation_integrity_scoring",
)

# FIX 170 sections FIX 175 reads via summary only — must not re-emit.
UPSTREAM_SECTIONS_OWNED_BY_FIX_170: Final[tuple[str, ...]] = (
    "human_decision_read",
    "bounded_work_envelope",
    "envelope_validation",
    "existing_gate_checks",
    "tier_boundary_enforcement",
    "reengagement_triggers",
    "forbidden_authorization_actions",
    "next_step_authorization_sequence",
    "authorization_integrity_scoring",
)

GOVERNED_LANE_READINESS_BOARD_RECORD_KINDS: Final[tuple[str, ...]] = (
    "lane_readiness_board_artifact",
    "board_candidate_note",
    "board_blocker_note",
    "board_gate_note",
    "board_escalation_note",
    "board_risk_note",
    "forbidden_board_note",
    "governed_lane_readiness_board_record",
)

GOVERNED_LANE_READINESS_BOARD_PRINCIPLES: Final[tuple[tuple[str, str], ...]] = (
    ("composes_upstream", "FIX 175 composes FIX 174 lane recommendation — never duplicates it."),
    ("board_not_decision", "Lane readiness board ≠ lane admission decision."),
    ("human_review_first", "Board consolidates eligibility for human admission review (FIX 176)."),
    ("recommendation_from_174", "Candidates, blockers, and gates surfaced from FIX 174 only."),
    ("envelope_from_170", "Authorization envelope status read from FIX 170 summary only."),
    ("no_lane_admission", "Board never performs lane admission or approval execution."),
    ("frozen_gates_only", "Required gates reference existing frozen gates."),
    ("no_lane_entry", "Board never autonomously enters governed lanes."),
    ("audit_replay_preserved", "Audit, replay, and receipt requirements are never reduced."),
)

FORBIDDEN_BOARD_ACTIONS: Final[tuple[tuple[str, str], ...]] = (
    ("lane_admission_decision", "Lane readiness board never makes lane admission decisions."),
    ("lane_admission", "Lane readiness board never performs lane admission."),
    ("lane_entry", "Lane readiness board never enters governed lanes."),
    ("approval_execution", "Lane readiness board never executes approvals."),
    ("approval_bypass", "Lane readiness board never bypasses existing approval gates."),
    ("code_write", "Lane readiness board never writes code."),
    ("pr_action", "Lane readiness board never performs PR actions."),
    ("merge_deploy", "Lane readiness board never merges or deploys."),
    ("railway_mutation", "Lane readiness board never mutates Railway infrastructure."),
    ("gate_bypass", "Lane readiness board never routes around frozen gates."),
    ("recommendation_recompute", "Lane readiness board never redefines FIX 174 recommendation sections."),
)

GOVERNED_LANE_READINESS_BOARD_EXECUTABLE: Final[bool] = False

MAX_GOVERNED_LANE_READINESS_BOARD_CONTENT_LEN: Final[int] = 4000
MAX_PERSISTED_GOVERNED_LANE_READINESS_BOARD_RECORDS: Final[int] = 500
