# SPDX-License-Identifier: Apache-2.0
"""FIX 179 — frozen gate execution request adapter contract (execution request ≠ execution)."""

from __future__ import annotations

from typing import Final

FROZEN_GATE_EXECUTION_REQUEST_ADAPTER_SCHEMA_VERSION: Final[str] = (
    "mission_control_frozen_gate_execution_request_adapter_v1"
)
FROZEN_GATE_EXECUTION_REQUEST_ADAPTER_RECORD_SCHEMA_VERSION: Final[str] = (
    "mission_control_frozen_gate_execution_request_adapter_record_v1"
)
FROZEN_GATE_EXECUTION_REQUEST_ADAPTER_FIX: Final[str] = "FIX 179"

MUTATION_PERFORMED_FIX_179: Final[bool] = False
EXECUTION_PERFORMED_FIX_179: Final[bool] = False
GATE_EXECUTION_PERFORMED_FIX_179: Final[bool] = False
COMMAND_EXECUTION_PERFORMED_FIX_179: Final[bool] = False
LANE_ENTRY_EXECUTION_PERFORMED_FIX_179: Final[bool] = False
LANE_ADMISSION_EXECUTED_FIX_179: Final[bool] = False
AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_179: Final[bool] = False
AUTONOMOUS_EXECUTION_ENABLED_FIX_179: Final[bool] = False
AUTONOMOUS_LANE_ENTRY_ENABLED_FIX_179: Final[bool] = False
AUTONOMOUS_APPROVAL_ENABLED_FIX_179: Final[bool] = False
TIER_ESCALATION_ENABLED_FIX_179: Final[bool] = False
GATE_BYPASS_ENABLED_FIX_179: Final[bool] = False
CODE_WRITE_ENABLED_FIX_179: Final[bool] = False
PR_ACTION_ENABLED_FIX_179: Final[bool] = False
MERGE_DEPLOY_ENABLED_FIX_179: Final[bool] = False
RAILWAY_MUTATION_ENABLED_FIX_179: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_179: Final[bool] = False

FROZEN_GATE_EXECUTION_REQUEST_ADAPTER_ROUTE_ID: Final[str] = (
    "mission_control_frozen_gate_execution_request_adapter"
)

FROZEN_GATE_EXECUTION_REQUEST_ADAPTER_INVARIANT: Final[str] = (
    "frozen_gate_execution_request_adapter_converts_fix_178_intake_preview_into_frozen_gate_execution_request_without_command_execution_or_approval_bypass"
)

EXECUTION_REQUEST_TIER: Final[str] = "tier_1_tier_2_bounded"

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

# Section keys owned by FIX 178 — FIX 179 must never emit these (composition only).
UPSTREAM_SECTIONS_OWNED_BY_FIX_178: Final[tuple[str, ...]] = (
    "handoff_upstream_read",
    "matching_frozen_gate_identification",
    "intake_preview_packet",
    "packet_shape_validation",
    "required_existing_commands",
    "missing_gate_prerequisites",
    "lane_entry_confirmation",
    "forbidden_intake_actions",
    "next_step_intake_sequence",
    "intake_integrity_scoring",
)

# Maps frozen gate id → exact existing lane command (adapter never executes).
GATE_FROZEN_COMMAND_MAP: Final[dict[str, dict[str, str | bool]]] = {
    "issue_intake": {
        "primary_frozen_command": "show issue plan",
        "software_delivery_route": "issue_planning",
        "approval_phrase_required": False,
    },
    "implementation_plan": {
        "primary_frozen_command": "show implementation plan",
        "software_delivery_route": "issue_planning",
        "approval_phrase_required": False,
    },
    "planning_approved": {
        "primary_frozen_command": "approve planning",
        "software_delivery_route": "issue_planning",
        "approval_phrase_required": True,
        "approval_phrase_contract": "PLANNING_APPROVAL_PHRASE",
    },
    "patch_proposal_approved": {
        "primary_frozen_command": "approve patch proposal",
        "software_delivery_route": "patch_proposal",
        "approval_phrase_required": True,
        "approval_phrase_contract": "PATCH_PROPOSAL_APPROVAL_PHRASE",
    },
    "workspace_apply_approved": {
        "primary_frozen_command": "approve workspace apply",
        "software_delivery_route": "workspace_apply",
        "approval_phrase_required": True,
        "approval_phrase_contract": "WORKSPACE_APPLY_APPROVAL_PHRASE",
    },
    "workspace_verification": {
        "primary_frozen_command": "run workspace verification",
        "software_delivery_route": "workspace_verification",
        "approval_phrase_required": False,
    },
    "github_preflight_approved": {
        "primary_frozen_command": "approve github pr preflight",
        "software_delivery_route": "github_pr_preflight",
        "approval_phrase_required": True,
        "approval_phrase_contract": "GITHUB_PR_PREFLIGHT_APPROVAL_PHRASE",
    },
    "software_delivery-stage": {
        "primary_frozen_command": "show software delivery timeline",
        "software_delivery_route": "software_delivery",
        "approval_phrase_required": False,
    },
}

GATE_BLAST_RADIUS_SUMMARY: Final[dict[str, dict[str, str]]] = {
    "workspace_verification": {
        "tier": "tier_1_2_bounded",
        "scope": "workspace_read_only_checks",
        "detail": "Verification reads workspace state — no merge, deploy, or Railway mutation.",
    },
    "workspace_apply_approved": {
        "tier": "tier_1_2_bounded",
        "scope": "governed_workspace_mutation",
        "detail": "Workspace apply mutates governed workspace only after explicit approval phrase.",
    },
    "github_preflight_approved": {
        "tier": "tier_1_2_bounded",
        "scope": "github_pr_preflight_read",
        "detail": "Preflight checks GitHub state — PR open requires separate governed approval.",
    },
}

FROZEN_GATE_EXECUTION_REQUEST_ADAPTER_RECORD_KINDS: Final[tuple[str, ...]] = (
    "execution_request_artifact",
    "command_mapping_note",
    "approval_phrase_note",
    "prerequisite_request_note",
    "audit_link_note",
    "forbidden_request_note",
    "frozen_gate_execution_request_record",
)

FROZEN_GATE_EXECUTION_REQUEST_ADAPTER_PRINCIPLES: Final[tuple[tuple[str, str], ...]] = (
    ("composes_upstream", "FIX 179 composes FIX 178 intake preview — never duplicates it."),
    ("request_not_execution", "Execution request ≠ command execution."),
    ("preview_required", "Execution request requires FIX 178 intake preview."),
    ("frozen_commands_only", "Adapter maps to existing frozen lane commands — never new routes."),
    ("approval_preserved", "Existing approval phrases and gates preserved — no bypass."),
    ("prerequisites_visible", "Missing prerequisites included in request artifact."),
    ("blast_radius_bounded", "Risk and blast-radius summary included for operator review."),
    ("audit_replay_linked", "Audit and replay linkage preserved for governed handoff."),
    ("no_autonomous_execution", "Adapter never autonomously executes frozen gate commands."),
)

FORBIDDEN_REQUEST_ACTIONS: Final[tuple[tuple[str, str], ...]] = (
    ("command_execution", "Execution request adapter never executes frozen gate commands."),
    ("gate_execution", "Execution request adapter never performs gate execution."),
    ("lane_entry_execution", "Execution request adapter never executes lane entry."),
    ("approval_execution", "Execution request adapter never executes approvals."),
    ("approval_bypass", "Execution request adapter never bypasses approval gates."),
    ("gate_bypass", "Execution request adapter never routes around frozen gates."),
    ("autonomous_request", "System never autonomously dispatches execution requests."),
    ("code_write", "Execution request adapter never writes code."),
    ("pr_action", "Execution request adapter never performs PR actions."),
    ("merge_deploy", "Execution request adapter never merges or deploys."),
    ("railway_mutation", "Execution request adapter never mutates Railway infrastructure."),
    ("intake_preview_recompute", "Execution request adapter never redefines FIX 178 preview sections."),
)

FROZEN_GATE_EXECUTION_REQUEST_ADAPTER_EXECUTABLE: Final[bool] = False

MAX_FROZEN_GATE_EXECUTION_REQUEST_ADAPTER_CONTENT_LEN: Final[int] = 4000
MAX_PERSISTED_FROZEN_GATE_EXECUTION_REQUEST_ADAPTER_RECORDS: Final[int] = 500
