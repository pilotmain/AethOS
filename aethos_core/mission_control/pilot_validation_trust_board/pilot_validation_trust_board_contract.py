# SPDX-License-Identifier: Apache-2.0
"""FIX 183 — pilot validation and trust board contract."""

from __future__ import annotations

from typing import Final

PILOT_VALIDATION_TRUST_BOARD_SCHEMA_VERSION: Final[str] = (
    "mission_control_pilot_validation_trust_board_v1"
)
PILOT_VALIDATION_TRUST_BOARD_RECORD_SCHEMA_VERSION: Final[str] = (
    "mission_control_pilot_validation_trust_board_record_v1"
)
PILOT_VALIDATION_TRUST_BOARD_FIX: Final[str] = "FIX 183"

MUTATION_PERFORMED_FIX_183: Final[bool] = False
EXECUTION_PERFORMED_FIX_183: Final[bool] = False
DIRECT_EXECUTION_PERFORMED_FIX_183: Final[bool] = False
DIRECT_PROVIDER_MUTATION_PERFORMED_FIX_183: Final[bool] = False
PILOT_REEXECUTION_PERFORMED_FIX_183: Final[bool] = False
AUTONOMOUS_VALIDATION_EXECUTION_ENABLED_FIX_183: Final[bool] = False
HIDDEN_PILOT_REEXECUTION_PERFORMED_FIX_183: Final[bool] = False
GATE_BYPASS_ENABLED_FIX_183: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_183: Final[bool] = False

VALIDATION_COMPOSES_AUDITS_ONLY_FIX_183: Final[bool] = True
PILOT_VALIDATION_TRUST_BOARD_ORIGIN: Final[str] = "mission_control_pilot_validation_trust_board"

PILOT_VALIDATION_TRUST_BOARD_ROUTE_ID: Final[str] = "mission_control_pilot_validation_trust_board"

PILOT_VALIDATION_TRUST_BOARD_INVARIANT: Final[str] = (
    "pilot_validation_trust_board_composes_fix_181_pilot_run_audits_and_artifacts_without_pilot_reexecution_or_provider_mutation"
)

PILOT_TERMINAL_STAGE_FIX_183: Final[str] = "pr_open"

TRUST_RECOMMENDATIONS: Final[tuple[str, ...]] = ("yes", "conditional", "no")

# Section keys owned by FIX 181 — FIX 183 must never emit these (composition only).
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

PILOT_VALIDATION_TRUST_BOARD_RECORD_KINDS: Final[tuple[str, ...]] = (
    "validation_artifact",
    "trust_note",
    "operator_effort_note",
    "validation_record",
)

PILOT_VALIDATION_TRUST_BOARD_PRINCIPLES: Final[tuple[tuple[str, str], ...]] = (
    ("composes_upstream", "FIX 183 composes FIX 181 pilot audits — never re-executes pilots."),
    ("validation_not_execution", "Validation board ≠ pilot re-execution."),
    ("audit_composition_only", "Trust metrics derived from persisted pilot run audits only."),
    ("stage_completion_visible", "Stages completed and stage stopped at surfaced for operator review."),
    ("approval_friction_visible", "Approval count and re-engagement count measured from chat steps."),
    ("manual_intervention_visible", "Manual intervention points listed from partial runs and blockers."),
    ("elapsed_time_visible", "Elapsed time computed across pilot audit timestamps."),
    ("evidence_completeness_visible", "Evidence bundle completeness scored without regeneration."),
    ("human_effort_scored", "Human effort score derived from operator touches — lower is better."),
    ("trust_recommendation", "Trust recommendation (yes | conditional | no) from pilot evidence."),
)

FORBIDDEN_VALIDATION_ACTIONS: Final[tuple[tuple[str, str], ...]] = (
    ("pilot_reexecution", "Validation board never re-runs pilot harness."),
    ("direct_provider_mutation", "Validation board never mutates providers."),
    ("hidden_pilot_run", "Validation board never autonomously runs pilots."),
    ("gate_bypass", "Validation board never bypasses frozen gates."),
    ("approval_bypass", "Validation board never bypasses approval phrases."),
    ("merge", "Validation board never merges pull requests."),
    ("deploy", "Validation board never deploys."),
    ("railway_mutation", "Validation board never mutates Railway infrastructure."),
    ("pilot_section_recompute", "Validation board never redefines FIX 181 pilot sections."),
)

PILOT_VALIDATION_TRUST_BOARD_EXECUTABLE: Final[bool] = False

MAX_PILOT_VALIDATION_TRUST_BOARD_CONTENT_LEN: Final[int] = 4000
MAX_PERSISTED_PILOT_VALIDATION_TRUST_BOARD_RECORDS: Final[int] = 500
