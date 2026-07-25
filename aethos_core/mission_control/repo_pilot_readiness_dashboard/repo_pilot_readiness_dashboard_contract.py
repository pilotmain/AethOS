# SPDX-License-Identifier: Apache-2.0
"""FIX 182 — repo pilot readiness dashboard contract."""

from __future__ import annotations

from typing import Final

REPO_PILOT_READINESS_DASHBOARD_SCHEMA_VERSION: Final[str] = (
    "mission_control_repo_pilot_readiness_dashboard_v1"
)
REPO_PILOT_READINESS_DASHBOARD_RECORD_SCHEMA_VERSION: Final[str] = (
    "mission_control_repo_pilot_readiness_dashboard_record_v1"
)
REPO_PILOT_READINESS_DASHBOARD_FIX: Final[str] = "FIX 182"

MUTATION_PERFORMED_FIX_182: Final[bool] = False
EXECUTION_PERFORMED_FIX_182: Final[bool] = False
DIRECT_EXECUTION_PERFORMED_FIX_182: Final[bool] = False
DIRECT_PROVIDER_MUTATION_PERFORMED_FIX_182: Final[bool] = False
PILOT_EXECUTION_PERFORMED_FIX_182: Final[bool] = False
AUTONOMOUS_READINESS_MUTATION_ENABLED_FIX_182: Final[bool] = False
HIDDEN_PILOT_EXECUTION_PERFORMED_FIX_182: Final[bool] = False
GATE_BYPASS_ENABLED_FIX_182: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_182: Final[bool] = False

READINESS_VISIBILITY_ONLY_FIX_182: Final[bool] = True
REPO_PILOT_READINESS_DASHBOARD_ORIGIN: Final[str] = "mission_control_repo_pilot_readiness_dashboard"

REPO_PILOT_READINESS_DASHBOARD_ROUTE_ID: Final[str] = "mission_control_repo_pilot_readiness_dashboard"

REPO_PILOT_READINESS_DASHBOARD_INVARIANT: Final[str] = (
    "repo_pilot_readiness_dashboard_surfaces_pilot_preflight_readiness_from_fix_181_without_pilot_execution_or_provider_mutation"
)

# Section keys owned by FIX 181 — FIX 182 must never emit these (composition only).
UPSTREAM_SECTIONS_OWNED_BY_FIX_181: Final[tuple[str, ...]] = (
    "handoff_invocation_upstream_read",
    "pilot_configuration",
    "pilot_stage_status_matrix",
    "governed_pilot_packet",
    "mission_control_timeline_capture",
    "evidence_bundle_capture",
    "approval_friction_verification",
    "missing_prerequisites_at_pilot",
    "risk_blast_radius_at_pilot",
    "audit_replay_linkage_at_pilot",
    "pilot_origin_logging",
    "forbidden_pilot_actions",
    "next_step_pilot_sequence",
    "pilot_integrity_scoring",
)

REPO_PILOT_READINESS_DASHBOARD_RECORD_KINDS: Final[tuple[str, ...]] = (
    "readiness_artifact",
    "repo_selection_note",
    "issue_selection_note",
    "preflight_note",
    "blocker_note",
    "forbidden_readiness_note",
    "repo_pilot_readiness_dashboard_record",
)

REPO_PILOT_READINESS_DASHBOARD_PRINCIPLES: Final[tuple[tuple[str, str], ...]] = (
    ("composes_upstream", "FIX 182 composes FIX 181 pilot harness — never duplicates it."),
    ("readiness_not_execution", "Readiness dashboard ≠ pilot execution."),
    ("visibility_only", "Dashboard surfaces preflight readiness — no stage advancement."),
    ("repo_issue_selection", "Repo and issue selection visible before pilot run."),
    ("auth_visible", "GitHub auth and branch permission readiness surfaced."),
    ("workspace_visible", "Workspace and verification command readiness surfaced."),
    ("pr_visible", "PR creation readiness surfaced without opening PRs."),
    ("evidence_visible", "Mission Control evidence readiness surfaced."),
    ("approval_summary", "Approval-friction summary preserved for operator review."),
    ("blocker_list", "Pilot blocker list aggregated for clean preflight."),
)

FORBIDDEN_READINESS_ACTIONS: Final[tuple[tuple[str, str], ...]] = (
    ("pilot_execution", "Readiness dashboard never runs pilot harness."),
    ("direct_provider_mutation", "Readiness dashboard never mutates providers."),
    ("hidden_pilot_run", "Readiness dashboard never autonomously runs pilots."),
    ("gate_bypass", "Readiness dashboard never bypasses frozen gates."),
    ("approval_bypass", "Readiness dashboard never bypasses approval phrases."),
    ("merge", "Readiness dashboard never merges pull requests."),
    ("deploy", "Readiness dashboard never deploys."),
    ("railway_mutation", "Readiness dashboard never mutates Railway infrastructure."),
    ("pilot_section_recompute", "Readiness dashboard never redefines FIX 181 pilot sections."),
)

REPO_PILOT_READINESS_DASHBOARD_EXECUTABLE: Final[bool] = False

MAX_REPO_PILOT_READINESS_DASHBOARD_CONTENT_LEN: Final[int] = 4000
MAX_PERSISTED_REPO_PILOT_READINESS_DASHBOARD_RECORDS: Final[int] = 500
