# SPDX-License-Identifier: Apache-2.0
"""FIX 174 — governed lane entry recommendation contract (recommendation ≠ admission)."""

from __future__ import annotations

from typing import Final

GOVERNED_LANE_ENTRY_RECOMMENDATION_SCHEMA_VERSION: Final[str] = (
    "mission_control_governed_lane_entry_recommendation_v1"
)
GOVERNED_LANE_ENTRY_RECOMMENDATION_RECORD_SCHEMA_VERSION: Final[str] = (
    "mission_control_governed_lane_entry_recommendation_record_v1"
)
GOVERNED_LANE_ENTRY_RECOMMENDATION_FIX: Final[str] = "FIX 174"

MUTATION_PERFORMED_FIX_174: Final[bool] = False
EXECUTION_PERFORMED_FIX_174: Final[bool] = False
LANE_ADMISSION_PERFORMED_FIX_174: Final[bool] = False
AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_174: Final[bool] = False
AUTONOMOUS_EXECUTION_ENABLED_FIX_174: Final[bool] = False
AUTONOMOUS_LANE_ENTRY_ENABLED_FIX_174: Final[bool] = False
AUTONOMOUS_APPROVAL_ENABLED_FIX_174: Final[bool] = False
TIER_ESCALATION_ENABLED_FIX_174: Final[bool] = False
GATE_BYPASS_ENABLED_FIX_174: Final[bool] = False
CODE_WRITE_ENABLED_FIX_174: Final[bool] = False
PR_ACTION_ENABLED_FIX_174: Final[bool] = False
MERGE_DEPLOY_ENABLED_FIX_174: Final[bool] = False
RAILWAY_MUTATION_ENABLED_FIX_174: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_174: Final[bool] = False

GOVERNED_LANE_ENTRY_RECOMMENDATION_ROUTE_ID: Final[str] = (
    "mission_control_governed_lane_entry_recommendation"
)

GOVERNED_LANE_ENTRY_RECOMMENDATION_INVARIANT: Final[str] = (
    "governed_lane_entry_recommendation_composes_fix_169_readiness_and_fix_173_gate_review_to_recommend_lane_entry_without_admission_or_execution_authority"
)

RECOMMENDATION_TIER: Final[str] = "tier_1_tier_2_bounded"

# Section keys owned by upstream layers — FIX 174 must never emit these (composition only).
UPSTREAM_SECTIONS_OWNED_BY_FIX_169: Final[tuple[str, ...]] = (
    "package_readiness_checks",
    "package_readiness_by_role",
    "lane_admission_analysis",
    "admission_blockers",
    "lane_admission_package",
    "admission_forbidden_actions",
    "admission_artifact_registry",
    "next_step_admission_sequence",
    "admission_integrity_scoring",
)

UPSTREAM_SECTIONS_OWNED_BY_FIX_173: Final[tuple[str, ...]] = (
    "coordination_context_read",
    "package_outcome_collection",
    "outcome_quality_classification",
    "incomplete_package_detection",
    "escalation_trigger_detection",
    "frozen_gate_mapping",
    "gate_review_packet",
    "gate_handler_routing",
    "forbidden_review_actions",
    "next_step_gate_review_sequence",
    "gate_review_integrity_scoring",
)

FORBIDDEN_RECOMMENDATION_LANES: Final[tuple[str, ...]] = (
    "railway_orchestration",
    "production_governance",
)

GOVERNED_LANE_ENTRY_RECOMMENDATION_RECORD_KINDS: Final[tuple[str, ...]] = (
    "lane_recommendation_artifact",
    "eligibility_rationale_note",
    "blocked_lane_note",
    "escalation_recommendation_note",
    "next_gate_note",
    "forbidden_recommendation_note",
    "governed_lane_entry_recommendation_record",
)

GOVERNED_LANE_ENTRY_RECOMMENDATION_PRINCIPLES: Final[tuple[tuple[str, str], ...]] = (
    ("composes_upstream", "FIX 174 composes FIX 169 readiness and FIX 173 gate review — never duplicates them."),
    ("recommendation_not_admission", "Lane recommendation ≠ lane admission authority."),
    ("recommendation_not_execution", "Lane recommendation never performs lane execution."),
    ("readiness_from_169", "Structural readiness signals read from FIX 169 only."),
    ("outcomes_from_173", "Outcome quality and gate packet read from FIX 173 only."),
    ("frozen_gates_only", "Recommended next gate references existing frozen gates."),
    ("blocked_explained", "Blocked lanes explained with prerequisite references from upstream."),
    ("no_lane_entry", "Recommendation never autonomously enters governed lanes."),
    ("audit_replay_preserved", "Audit, replay, and receipt requirements are never reduced."),
)

FORBIDDEN_RECOMMENDATION_ACTIONS: Final[tuple[tuple[str, str], ...]] = (
    ("lane_admission", "Lane recommendation never performs lane admission."),
    ("lane_entry", "Lane recommendation never enters governed lanes."),
    ("approval_execution", "Lane recommendation never executes approvals."),
    ("approval_bypass", "Lane recommendation never bypasses existing approval gates."),
    ("code_write", "Lane recommendation never writes code."),
    ("pr_action", "Lane recommendation never performs PR actions."),
    ("merge_deploy", "Lane recommendation never merges or deploys."),
    ("railway_mutation", "Lane recommendation never mutates Railway infrastructure."),
    ("gate_bypass", "Lane recommendation never routes around frozen gates."),
    ("readiness_recompute", "Lane recommendation never redefines FIX 169 readiness sections."),
    ("outcome_reclassify", "Lane recommendation never reclassifies FIX 173 outcome quality."),
)

GOVERNED_LANE_ENTRY_RECOMMENDATION_EXECUTABLE: Final[bool] = False

MAX_GOVERNED_LANE_ENTRY_RECOMMENDATION_CONTENT_LEN: Final[int] = 4000
MAX_PERSISTED_GOVERNED_LANE_ENTRY_RECOMMENDATION_RECORDS: Final[int] = 500
