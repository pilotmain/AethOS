# SPDX-License-Identifier: Apache-2.0
"""FIX 178 — frozen gate intake preview contract (intake preview ≠ gate execution)."""

from __future__ import annotations

from typing import Final

FROZEN_GATE_INTAKE_PREVIEW_SCHEMA_VERSION: Final[str] = "mission_control_frozen_gate_intake_preview_v1"
FROZEN_GATE_INTAKE_PREVIEW_RECORD_SCHEMA_VERSION: Final[str] = (
    "mission_control_frozen_gate_intake_preview_record_v1"
)
FROZEN_GATE_INTAKE_PREVIEW_FIX: Final[str] = "FIX 178"

MUTATION_PERFORMED_FIX_178: Final[bool] = False
EXECUTION_PERFORMED_FIX_178: Final[bool] = False
GATE_EXECUTION_PERFORMED_FIX_178: Final[bool] = False
LANE_ENTRY_EXECUTION_PERFORMED_FIX_178: Final[bool] = False
LANE_ADMISSION_EXECUTED_FIX_178: Final[bool] = False
AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_178: Final[bool] = False
AUTONOMOUS_EXECUTION_ENABLED_FIX_178: Final[bool] = False
AUTONOMOUS_LANE_ENTRY_ENABLED_FIX_178: Final[bool] = False
AUTONOMOUS_APPROVAL_ENABLED_FIX_178: Final[bool] = False
TIER_ESCALATION_ENABLED_FIX_178: Final[bool] = False
GATE_BYPASS_ENABLED_FIX_178: Final[bool] = False
CODE_WRITE_ENABLED_FIX_178: Final[bool] = False
PR_ACTION_ENABLED_FIX_178: Final[bool] = False
MERGE_DEPLOY_ENABLED_FIX_178: Final[bool] = False
RAILWAY_MUTATION_ENABLED_FIX_178: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_178: Final[bool] = False

FROZEN_GATE_INTAKE_PREVIEW_ROUTE_ID: Final[str] = "mission_control_frozen_gate_intake_preview"

FROZEN_GATE_INTAKE_PREVIEW_INVARIANT: Final[str] = (
    "frozen_gate_intake_preview_receives_fix_177_handoff_packet_and_previews_frozen_gate_intake_without_gate_execution_or_lane_entry"
)

INTAKE_PREVIEW_TIER: Final[str] = "tier_1_tier_2_bounded"

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

# Section keys owned by FIX 177 — FIX 178 must never emit these (composition only).
UPSTREAM_SECTIONS_OWNED_BY_FIX_177: Final[tuple[str, ...]] = (
    "human_decision_upstream_read",
    "target_frozen_gate_identification",
    "decision_rationale_in_handoff",
    "accepted_risks_in_handoff",
    "remaining_blockers_in_handoff",
    "gate_validation_requirements",
    "required_next_commands",
    "gate_handoff_packet",
    "forbidden_handoff_actions",
    "next_step_handoff_sequence",
    "handoff_integrity_scoring",
)

HANDOFF_PACKET_SHAPE_FIELDS: Final[tuple[str, ...]] = (
    "packet_id",
    "decision_value",
    "target_gate_id",
    "handoff_ready",
    "lane_entry_execution_performed",
    "gate_bypass",
    "approval_bypass",
)

GATE_EXISTING_COMMAND_HINTS: Final[dict[str, tuple[tuple[str, str], ...]]] = {
    "issue_intake": (("show issue plan", "Read issue plan state (frozen lane)."),),
    "implementation_plan": (("show implementation plan", "Read implementation plan (frozen lane)."),),
    "planning_approved": (("approve planning", "Governed planning approval phrase (frozen gate)."),),
    "patch_proposal_approved": (
        ("show patch proposal", "Read patch proposal (frozen lane)."),
        ("approve patch proposal", "Governed patch approval phrase (frozen gate)."),
    ),
    "workspace_apply_approved": (
        ("show workspace status", "Read workspace apply state (frozen lane)."),
        ("approve workspace apply", "Governed workspace apply phrase (frozen gate)."),
    ),
    "workspace_verification": (
        ("show workspace verification status", "Read verification state (frozen lane)."),
        ("run workspace verification", "Execute verification after prerequisites (frozen gate)."),
    ),
    "github_preflight_approved": (
        ("show github pr preflight", "Read preflight state (frozen lane)."),
        ("approve github pr preflight", "Governed preflight approval phrase (frozen gate)."),
    ),
    "software_delivery-stage": (
        ("show software delivery timeline", "Read delivery timeline (frozen lane)."),
    ),
}

FROZEN_GATE_INTAKE_PREVIEW_RECORD_KINDS: Final[tuple[str, ...]] = (
    "intake_preview_artifact",
    "gate_match_note",
    "prerequisite_note",
    "intake_command_note",
    "forbidden_intake_note",
    "frozen_gate_intake_preview_record",
)

FROZEN_GATE_INTAKE_PREVIEW_PRINCIPLES: Final[tuple[tuple[str, str], ...]] = (
    ("composes_upstream", "FIX 178 composes FIX 177 gate handoff packet — never duplicates it."),
    ("preview_not_execution", "Gate intake preview ≠ gate execution."),
    ("handoff_required", "Intake preview requires FIX 177 handoff packet."),
    ("frozen_gates_only", "Preview targets existing frozen gates — never around them."),
    ("shape_validation", "Handoff packet shape validated before preview."),
    ("prerequisites_visible", "Missing gate prerequisites listed for operator."),
    ("commands_advisory", "Required existing commands listed — never executed here."),
    ("no_lane_entry", "Intake preview never performs lane entry."),
    ("audit_replay_preserved", "Audit, replay, and receipt requirements are never reduced."),
)

FORBIDDEN_INTAKE_ACTIONS: Final[tuple[tuple[str, str], ...]] = (
    ("gate_execution", "Intake preview never executes frozen gate actions."),
    ("lane_entry_execution", "Intake preview never executes lane entry."),
    ("lane_admission_execution", "Intake preview never performs lane admission."),
    ("approval_execution", "Intake preview never executes approvals."),
    ("approval_bypass", "Intake preview never bypasses existing approval gates."),
    ("gate_bypass", "Intake preview never routes around frozen gates."),
    ("autonomous_intake", "System never autonomously executes gate intake."),
    ("code_write", "Intake preview never writes code."),
    ("pr_action", "Intake preview never performs PR actions."),
    ("merge_deploy", "Intake preview never merges or deploys."),
    ("railway_mutation", "Intake preview never mutates Railway infrastructure."),
    ("handoff_recompute", "Intake preview never redefines FIX 177 handoff sections."),
)

FROZEN_GATE_INTAKE_PREVIEW_EXECUTABLE: Final[bool] = False

MAX_FROZEN_GATE_INTAKE_PREVIEW_CONTENT_LEN: Final[int] = 4000
MAX_PERSISTED_FROZEN_GATE_INTAKE_PREVIEW_RECORDS: Final[int] = 500
