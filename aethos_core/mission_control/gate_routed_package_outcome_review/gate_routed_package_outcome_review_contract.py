# SPDX-License-Identifier: Apache-2.0
"""FIX 173 — gate-routed package outcome review contract (review before lane action)."""

from __future__ import annotations

from typing import Final

GATE_ROUTED_PACKAGE_OUTCOME_REVIEW_SCHEMA_VERSION: Final[str] = (
    "mission_control_gate_routed_package_outcome_review_v1"
)
GATE_ROUTED_PACKAGE_OUTCOME_REVIEW_RECORD_SCHEMA_VERSION: Final[str] = (
    "mission_control_gate_routed_package_outcome_review_record_v1"
)
GATE_ROUTED_PACKAGE_OUTCOME_REVIEW_FIX: Final[str] = "FIX 173"

MUTATION_PERFORMED_FIX_173: Final[bool] = False
EXECUTION_PERFORMED_FIX_173: Final[bool] = False
AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_173: Final[bool] = False
AUTONOMOUS_EXECUTION_ENABLED_FIX_173: Final[bool] = False
AUTONOMOUS_LANE_ENTRY_ENABLED_FIX_173: Final[bool] = False
AUTONOMOUS_APPROVAL_ENABLED_FIX_173: Final[bool] = False
TIER_ESCALATION_ENABLED_FIX_173: Final[bool] = False
GATE_BYPASS_ENABLED_FIX_173: Final[bool] = False
CODE_WRITE_ENABLED_FIX_173: Final[bool] = False
PR_ACTION_ENABLED_FIX_173: Final[bool] = False
MERGE_DEPLOY_ENABLED_FIX_173: Final[bool] = False
RAILWAY_MUTATION_ENABLED_FIX_173: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_173: Final[bool] = False

GATE_ROUTED_PACKAGE_OUTCOME_REVIEW_ROUTE_ID: Final[str] = (
    "mission_control_gate_routed_package_outcome_review"
)

GATE_ROUTED_PACKAGE_OUTCOME_REVIEW_INVARIANT: Final[str] = (
    "gate_routed_package_outcome_review_collects_and_classifies_coordination_outcomes_and_maps_them_to_existing_frozen_gates_without_execution_or_bypass"
)

REVIEW_TIER: Final[str] = "tier_1_tier_2_bounded"

OUTCOME_QUALITY_LABELS: Final[tuple[str, ...]] = (
    "complete",
    "partial",
    "incomplete",
    "blocked",
    "escalated",
)

FORBIDDEN_REVIEW_LANES: Final[tuple[str, ...]] = (
    "railway_orchestration",
    "production_governance",
)

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

GATE_ROUTED_PACKAGE_OUTCOME_REVIEW_RECORD_KINDS: Final[tuple[str, ...]] = (
    "gate_review_artifact",
    "outcome_quality_note",
    "incomplete_package_note",
    "escalation_review_note",
    "gate_mapping_note",
    "forbidden_review_note",
    "gate_routed_package_outcome_review_record",
)

GATE_ROUTED_PACKAGE_OUTCOME_REVIEW_PRINCIPLES: Final[tuple[tuple[str, str], ...]] = (
    ("coordination_required", "Gate review requires FIX 172 governed task execution coordination context."),
    ("review_not_execution", "Outcome review classifies and maps — it never performs lane execution."),
    ("outcomes_from_coordination", "Package outcomes collected from coordination without mutation."),
    ("quality_classified", "Outcome quality classified without approval bypass."),
    ("incomplete_detected", "Incomplete packages detected with escalation triggers."),
    ("frozen_gates_only", "Outcomes map to existing frozen gates — never around them."),
    ("gate_review_packet", "Gate review packet produced for operator handoff to lanes."),
    ("no_lane_entry", "Review never autonomously enters governed lanes."),
    ("audit_replay_preserved", "Audit, replay, and receipt requirements are never reduced."),
)

FORBIDDEN_REVIEW_ACTIONS: Final[tuple[tuple[str, str], ...]] = (
    ("execution", "Gate review never performs execution."),
    ("approval_bypass", "Gate review never bypasses existing approval gates."),
    ("code_write", "Gate review never writes code."),
    ("pr_action", "Gate review never performs PR actions."),
    ("merge_deploy", "Gate review never merges or deploys."),
    ("railway_mutation", "Gate review never mutates Railway infrastructure."),
    ("autonomous_lane_entry", "Gate review never autonomously enters governed lanes."),
    ("gate_bypass", "Gate review never routes around frozen gates."),
)

GATE_ROUTED_PACKAGE_OUTCOME_REVIEW_EXECUTABLE: Final[bool] = False

MAX_GATE_ROUTED_PACKAGE_OUTCOME_REVIEW_CONTENT_LEN: Final[int] = 4000
MAX_PERSISTED_GATE_ROUTED_PACKAGE_OUTCOME_REVIEW_RECORDS: Final[int] = 500
