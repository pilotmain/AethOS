# SPDX-License-Identifier: Apache-2.0
"""FIX 181 — end-to-end repo development pilot harness contract."""

from __future__ import annotations

from typing import Final

END_TO_END_REPO_DEVELOPMENT_PILOT_HARNESS_SCHEMA_VERSION: Final[str] = (
    "mission_control_end_to_end_repo_development_pilot_harness_v1"
)
END_TO_END_REPO_DEVELOPMENT_PILOT_HARNESS_RECORD_SCHEMA_VERSION: Final[str] = (
    "mission_control_end_to_end_repo_development_pilot_harness_record_v1"
)
END_TO_END_REPO_DEVELOPMENT_PILOT_HARNESS_FIX: Final[str] = "FIX 181"

MUTATION_PERFORMED_FIX_181: Final[bool] = False
EXECUTION_PERFORMED_FIX_181: Final[bool] = False
DIRECT_EXECUTION_PERFORMED_FIX_181: Final[bool] = False
DIRECT_PROVIDER_MUTATION_PERFORMED_FIX_181: Final[bool] = False
AUTONOMOUS_PIPELINE_EXECUTION_ENABLED_FIX_181: Final[bool] = False
HIDDEN_COMMAND_EXECUTION_PERFORMED_FIX_181: Final[bool] = False
GATE_BYPASS_ENABLED_FIX_181: Final[bool] = False
MERGE_ENABLED_FIX_181: Final[bool] = False
DEPLOY_ENABLED_FIX_181: Final[bool] = False
RAILWAY_MUTATION_ENABLED_FIX_181: Final[bool] = False
PRODUCTION_COUPLING_ENABLED_FIX_181: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_181: Final[bool] = False

CHAT_GOVERNANCE_REQUIRED_FIX_181: Final[bool] = True
PILOT_HARNESS_ORIGIN: Final[str] = "mission_control_end_to_end_repo_development_pilot_harness"
PILOT_HARNESS_CHANNEL: Final[str] = "mission_control_pilot_harness"

END_TO_END_REPO_DEVELOPMENT_PILOT_HARNESS_ROUTE_ID: Final[str] = (
    "mission_control_end_to_end_repo_development_pilot_harness"
)

END_TO_END_REPO_DEVELOPMENT_PILOT_HARNESS_INVARIANT: Final[str] = (
    "end_to_end_repo_development_pilot_harness_routes_software_delivery_stages_through_resolve_chat_turn_without_autonomous_pipeline_execution_or_production_coupling"
)

PILOT_DEFAULT_REPO: Final[str] = "pilotmain/AethOS"
PILOT_DEFAULT_ISSUE_NUMBER: Final[str] = "80"
PILOT_DEFAULT_REPO_ISSUE: Final[str] = f"{PILOT_DEFAULT_REPO}#{PILOT_DEFAULT_ISSUE_NUMBER}"

PILOT_MAX_REPO_COUNT: Final[int] = 1
PILOT_MAX_ISSUE_COUNT: Final[int] = 1
PILOT_MAX_CHAT_STEPS_PER_RUN: Final[int] = 32

PILOT_TERMINAL_STAGE: Final[str] = "pr_open"

# Section keys owned by FIX 180 — FIX 181 must never emit these (composition only).
UPSTREAM_SECTIONS_OWNED_BY_FIX_180: Final[tuple[str, ...]] = (
    "execution_request_upstream_read",
    "frozen_chat_command_build",
    "governed_invocation_packet",
    "approval_gate_preservation",
    "missing_prerequisites_at_invocation",
    "risk_blast_radius_at_invocation",
    "audit_replay_linkage_at_invocation",
    "chat_origin_logging",
    "forbidden_invocation_actions",
    "next_step_invocation_sequence",
    "invocation_integrity_scoring",
)

END_TO_END_REPO_DEVELOPMENT_PILOT_HARNESS_RECORD_KINDS: Final[tuple[str, ...]] = (
    "pilot_artifact",
    "pilot_repo_note",
    "pilot_issue_note",
    "pilot_scope_note",
    "pilot_report_note",
    "forbidden_pilot_note",
    "end_to_end_pilot_harness_record",
)

END_TO_END_REPO_DEVELOPMENT_PILOT_HARNESS_PRINCIPLES: Final[tuple[tuple[str, str], ...]] = (
    ("composes_upstream", "FIX 181 composes FIX 180 handoff invocation — never duplicates it."),
    ("pilot_not_autonomous", "Pilot harness ≠ autonomous pipeline execution."),
    ("one_repo_one_issue", "Pilot limited to one repo and one bounded issue."),
    ("chat_governance_only", "Stage advancement routes only through resolve_chat_turn."),
    ("approval_preserved", "Approval-friction gates and phrases preserved — no bypass."),
    ("timeline_captured", "Mission Control timeline captured in pilot artifact."),
    ("evidence_captured", "Evidence bundle captured for pilot audit."),
    ("replay_linked", "Replay linkage preserved on pilot runs."),
    ("no_merge_deploy", "No merge, deploy, or Railway mutation in pilot scope."),
    ("explicit_run", "Operator must explicitly run pilot — no hidden execution."),
)

FORBIDDEN_PILOT_ACTIONS: Final[tuple[tuple[str, str], ...]] = (
    ("autonomous_pipeline_execution", "Pilot harness never autonomously executes full pipeline."),
    ("direct_provider_mutation", "Pilot harness never mutates providers outside chat governance."),
    ("hidden_stage_advance", "Pilot harness never advances stages without explicit run."),
    ("gate_bypass", "Pilot harness never bypasses frozen gates."),
    ("approval_bypass", "Pilot harness never bypasses approval phrases."),
    ("merge", "Pilot harness never merges pull requests."),
    ("deploy", "Pilot harness never deploys."),
    ("railway_mutation", "Pilot harness never mutates Railway infrastructure."),
    ("production_coupling", "Pilot harness never couples to production governance lanes."),
    ("multi_repo_pilot", "Pilot harness never spans multiple repos in one run."),
    ("invocation_section_recompute", "Pilot harness never redefines FIX 180 invocation sections."),
)

END_TO_END_REPO_DEVELOPMENT_PILOT_HARNESS_EXECUTABLE: Final[bool] = False

MAX_END_TO_END_REPO_DEVELOPMENT_PILOT_HARNESS_CONTENT_LEN: Final[int] = 4000
MAX_PERSISTED_END_TO_END_REPO_DEVELOPMENT_PILOT_HARNESS_RECORDS: Final[int] = 500
