# SPDX-License-Identifier: Apache-2.0
"""FIX 180 — governed chat command invocation from handoff contract."""

from __future__ import annotations

from typing import Final

GOVERNED_CHAT_COMMAND_INVOCATION_FROM_HANDOFF_SCHEMA_VERSION: Final[str] = (
    "mission_control_governed_chat_command_invocation_from_handoff_v1"
)
GOVERNED_CHAT_COMMAND_INVOCATION_FROM_HANDOFF_RECORD_SCHEMA_VERSION: Final[str] = (
    "mission_control_governed_chat_command_invocation_from_handoff_record_v1"
)
GOVERNED_CHAT_COMMAND_INVOCATION_FROM_HANDOFF_FIX: Final[str] = "FIX 180"

MUTATION_PERFORMED_FIX_180: Final[bool] = False
EXECUTION_PERFORMED_FIX_180: Final[bool] = False
DIRECT_EXECUTION_PERFORMED_FIX_180: Final[bool] = False
DIRECT_PROVIDER_MUTATION_PERFORMED_FIX_180: Final[bool] = False
GATE_EXECUTION_PERFORMED_FIX_180: Final[bool] = False
HIDDEN_COMMAND_EXECUTION_PERFORMED_FIX_180: Final[bool] = False
LANE_ENTRY_EXECUTION_PERFORMED_FIX_180: Final[bool] = False
LANE_ADMISSION_EXECUTED_FIX_180: Final[bool] = False
AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_180: Final[bool] = False
AUTONOMOUS_EXECUTION_ENABLED_FIX_180: Final[bool] = False
AUTONOMOUS_LANE_ENTRY_ENABLED_FIX_180: Final[bool] = False
AUTONOMOUS_APPROVAL_ENABLED_FIX_180: Final[bool] = False
TIER_ESCALATION_ENABLED_FIX_180: Final[bool] = False
GATE_BYPASS_ENABLED_FIX_180: Final[bool] = False
CODE_WRITE_ENABLED_FIX_180: Final[bool] = False
PR_ACTION_ENABLED_FIX_180: Final[bool] = False
MERGE_DEPLOY_ENABLED_FIX_180: Final[bool] = False
RAILWAY_MUTATION_ENABLED_FIX_180: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_180: Final[bool] = False

CHAT_GOVERNANCE_REQUIRED_FIX_180: Final[bool] = True
HANDOFF_INVOCATION_ORIGIN: Final[str] = "mission_control_governed_chat_command_invocation_from_handoff"
HANDOFF_INVOCATION_CHANNEL: Final[str] = "mission_control_handoff"

GOVERNED_CHAT_COMMAND_INVOCATION_FROM_HANDOFF_ROUTE_ID: Final[str] = (
    "mission_control_governed_chat_command_invocation_from_handoff"
)

GOVERNED_CHAT_COMMAND_INVOCATION_FROM_HANDOFF_INVARIANT: Final[str] = (
    "governed_chat_command_invocation_from_handoff_routes_fix_179_execution_request_through_resolve_chat_turn_without_direct_provider_mutation_or_gate_bypass"
)

INVOCATION_TIER: Final[str] = "tier_1_tier_2_bounded"

# Section keys owned by FIX 179 — FIX 180 must never emit these (composition only).
UPSTREAM_SECTIONS_OWNED_BY_FIX_179: Final[tuple[str, ...]] = (
    "intake_preview_upstream_read",
    "frozen_gate_command_mapping",
    "gate_execution_request_artifact",
    "approval_phrase_preservation",
    "missing_prerequisites_in_request",
    "risk_blast_radius_summary",
    "audit_replay_linkage",
    "forbidden_request_actions",
    "next_step_request_sequence",
    "request_integrity_scoring",
)

GOVERNED_CHAT_COMMAND_INVOCATION_FROM_HANDOFF_RECORD_KINDS: Final[tuple[str, ...]] = (
    "invocation_artifact",
    "chat_command_note",
    "origin_log_note",
    "audit_link_note",
    "forbidden_invocation_note",
    "governed_chat_command_invocation_record",
)

GOVERNED_CHAT_COMMAND_INVOCATION_FROM_HANDOFF_PRINCIPLES: Final[tuple[tuple[str, str], ...]] = (
    ("composes_upstream", "FIX 180 composes FIX 179 execution request — never duplicates it."),
    ("invocation_not_direct", "Handoff invocation ≠ direct provider execution."),
    ("request_required", "Invocation requires FIX 179 execution request artifact."),
    ("chat_governance_only", "Commands invoke only through resolve_chat_turn governance route."),
    ("approval_preserved", "Existing approval phrases and gates preserved — no bypass."),
    ("origin_logged", "UI/chat handoff origin logged for audit."),
    ("replay_linked", "Audit and replay linkage preserved on invocation."),
    ("explicit_invoke", "No hidden command execution — operator must explicitly invoke."),
    ("no_provider_bypass", "No direct provider/API mutation from handoff layer."),
)

FORBIDDEN_INVOCATION_ACTIONS: Final[tuple[tuple[str, str], ...]] = (
    ("direct_provider_mutation", "Handoff invocation never mutates providers directly."),
    ("direct_api_execution", "Handoff invocation never bypasses chat governance APIs."),
    ("hidden_command_execution", "Handoff invocation never autonomously executes commands."),
    ("gate_bypass", "Handoff invocation never routes around frozen gates."),
    ("approval_bypass", "Handoff invocation never bypasses approval gates."),
    ("autonomous_invoke", "System never autonomously invokes frozen commands."),
    ("railway_mutation", "Handoff invocation never mutates Railway infrastructure."),
    ("merge_deploy", "Handoff invocation never merges or deploys."),
    ("pr_action_bypass", "Handoff invocation never opens PRs outside governed chat."),
    ("execution_request_recompute", "Handoff invocation never redefines FIX 179 request sections."),
)

GOVERNED_CHAT_COMMAND_INVOCATION_FROM_HANDOFF_EXECUTABLE: Final[bool] = False

MAX_GOVERNED_CHAT_COMMAND_INVOCATION_FROM_HANDOFF_CONTENT_LEN: Final[int] = 4000
MAX_PERSISTED_GOVERNED_CHAT_COMMAND_INVOCATION_FROM_HANDOFF_RECORDS: Final[int] = 500
