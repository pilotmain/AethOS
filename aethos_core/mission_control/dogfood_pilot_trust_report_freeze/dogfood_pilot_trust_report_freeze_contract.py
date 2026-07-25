# SPDX-License-Identifier: Apache-2.0
"""FIX 186 — dogfood pilot trust report freeze contract."""

from __future__ import annotations

from typing import Final

DOGFOOD_PILOT_TRUST_REPORT_FREEZE_SCHEMA_VERSION: Final[str] = (
    "mission_control_dogfood_pilot_trust_report_freeze_v1"
)
DOGFOOD_PILOT_TRUST_REPORT_FREEZE_RECORD_SCHEMA_VERSION: Final[str] = (
    "mission_control_dogfood_pilot_trust_report_freeze_record_v1"
)
DOGFOOD_PILOT_TRUST_REPORT_FREEZE_FIX: Final[str] = "FIX 186"

MUTATION_PERFORMED_FIX_186: Final[bool] = False
EXECUTION_PERFORMED_FIX_186: Final[bool] = False
DIRECT_EXECUTION_PERFORMED_FIX_186: Final[bool] = False
DIRECT_PROVIDER_MUTATION_PERFORMED_FIX_186: Final[bool] = False
PILOT_REEXECUTION_PERFORMED_FIX_186: Final[bool] = False
AUTONOMOUS_TRUST_REPORT_EXECUTION_ENABLED_FIX_186: Final[bool] = False
HIDDEN_PILOT_REEXECUTION_PERFORMED_FIX_186: Final[bool] = False
GATE_BYPASS_ENABLED_FIX_186: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_186: Final[bool] = False
MULTI_REPO_EXPANSION_BLOCKED_BY_DEFAULT_FIX_186: Final[bool] = True

TRUST_REPORT_COMPOSES_ARTIFACTS_ONLY_FIX_186: Final[bool] = True
DOGFOOD_PILOT_TRUST_REPORT_FREEZE_ORIGIN: Final[str] = (
    "mission_control_dogfood_pilot_trust_report_freeze"
)
DOGFOOD_PILOT_TRUST_REPORT_FREEZE_ROUTE_ID: Final[str] = (
    "mission_control_dogfood_pilot_trust_report_freeze"
)

DOGFOOD_PILOT_TRUST_REPORT_FREEZE_INVARIANT: Final[str] = (
    "dogfood_pilot_trust_report_freeze_composes_dogfood_pilot_1_3_artifacts_and_fix_183_metrics_without_pilot_reexecution_or_governance_authority"
)

DOGFOOD_REPO_ISSUE: Final[str] = "pilotmain/AethOS#1"
DOGFOOD_DOC_TARGET: Final[str] = "docs/AETHOS_DOGFOOD_AND_PILOT_VALIDATION_PRINCIPLE.md"

DOGFOOD_PILOT_SESSIONS: Final[tuple[str, ...]] = (
    "dogfood-pilot-1",
    "dogfood-pilot-2",
    "dogfood-pilot-3",
)

TRUST_STATUSES: Final[tuple[str, ...]] = (
    "CONDITIONALLY_TRUSTED",
    "NOT_TRUSTED",
    "PENDING_EVIDENCE",
)

TRUST_RECOMMENDATION_FIX_186: Final[str] = "CONDITIONALLY_TRUSTED"

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

UPSTREAM_SECTIONS_OWNED_BY_FIX_183: Final[tuple[str, ...]] = (
    "pilot_harness_upstream_read",
    "pilot_audit_composition",
    "stage_completion_summary",
    "approval_friction_metrics",
    "re_engagement_metrics",
    "manual_intervention_points",
    "elapsed_time_capture",
    "evidence_completeness_capture",
    "issue_risk_tier",
    "human_effort_scoring",
    "trust_recommendation",
    "audit_replay_linkage_at_validation",
    "forbidden_validation_actions",
    "validation_integrity_scoring",
)

DOGFOOD_PILOT_TRUST_REPORT_FREEZE_RECORD_KINDS: Final[tuple[str, ...]] = (
    "trust_report_freeze_artifact",
    "operator_review_note",
    "expansion_approval_note",
    "trust_boundary_note",
)

DOGFOOD_PILOT_TRUST_REPORT_FREEZE_PRINCIPLES: Final[tuple[tuple[str, str], ...]] = (
    ("trust_report_not_execution", "Trust report freeze ≠ pilot execution."),
    ("validation_not_reexecution", "Validation ≠ re-execution."),
    ("evidence_composition_not_authority", "Evidence composition ≠ governance authority."),
    ("frozen_timeline_visible", "Pilots 1–3 frozen timeline visible from composed artifacts."),
    ("trust_boundary_visible", "Conditionally trusted vs not-yet-trusted capabilities explicit."),
    ("expansion_blocked_by_default", "Multi-repo expansion blocked until operator review and approval."),
    ("no_inherited_trust", "Other repositories earn trust independently."),
    ("reproducible_from_artifacts", "Report reproducible from stored audits, receipts, and bundles."),
)

FORBIDDEN_TRUST_REPORT_ACTIONS: Final[tuple[tuple[str, str], ...]] = (
    ("pilot_reexecution", "Trust report freeze never re-runs pilot harness."),
    ("pilot_execution", "Trust report freeze never executes delivery loop stages."),
    ("direct_provider_mutation", "Trust report freeze never mutates providers."),
    ("hidden_pilot_run", "Trust report freeze never autonomously runs pilots."),
    ("gate_bypass", "Trust report freeze never bypasses frozen gates."),
    ("automatic_expansion", "Trust report freeze never auto-expands to other repositories."),
    ("inherited_trust", "Trust report freeze never grants inherited cross-repo trust."),
    ("merge", "Trust report freeze never merges pull requests."),
    ("deploy", "Trust report freeze never deploys."),
    ("railway_mutation", "Trust report freeze never mutates Railway infrastructure."),
    ("governance_mutation", "Trust report freeze never mutates governance state."),
)

DOGFOOD_PILOT_TRUST_REPORT_FREEZE_EXECUTABLE: Final[bool] = False

MAX_DOGFOOD_PILOT_TRUST_REPORT_FREEZE_CONTENT_LEN: Final[int] = 4000
MAX_PERSISTED_DOGFOOD_PILOT_TRUST_REPORT_FREEZE_RECORDS: Final[int] = 500

PROPOSED_MULTI_REPO_ORDER: Final[tuple[str, ...]] = (
    "pilotmain/AethOS",
    "pilotmain/pilot-os-ui",
    "pilotmain/atlas-trader",
    "pilotmain/nexora-monorepo-starter",
)
