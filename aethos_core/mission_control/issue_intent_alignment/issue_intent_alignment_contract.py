# SPDX-License-Identifier: Apache-2.0
"""FIX 184 — issue intent alignment and patch target validation contract."""

from __future__ import annotations

from typing import Final

ISSUE_INTENT_ALIGNMENT_SCHEMA_VERSION: Final[str] = "mission_control_issue_intent_alignment_v1"
ISSUE_INTENT_ALIGNMENT_RECORD_SCHEMA_VERSION: Final[str] = (
    "mission_control_issue_intent_alignment_record_v1"
)
ISSUE_INTENT_ALIGNMENT_FIX: Final[str] = "FIX 184"

MUTATION_PERFORMED_FIX_184: Final[bool] = False
EXECUTION_PERFORMED_FIX_184: Final[bool] = False
PATCH_EXECUTION_PERFORMED_FIX_184: Final[bool] = False
DIRECT_EXECUTION_PERFORMED_FIX_184: Final[bool] = False
DIRECT_PROVIDER_MUTATION_PERFORMED_FIX_184: Final[bool] = False
AUTONOMOUS_SCOPE_EXPANSION_ENABLED_FIX_184: Final[bool] = False
AUTONOMOUS_FILE_SELECTION_OVERRIDE_ENABLED_FIX_184: Final[bool] = False
AUTONOMOUS_AUTHORITY_ENABLED_FIX_184: Final[bool] = False
GATE_BYPASS_ENABLED_FIX_184: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_184: Final[bool] = False

ALIGNMENT_VALIDATION_PERFORMED_FIX_184: Final[bool] = True
ISSUE_INTENT_ALIGNMENT_ORIGIN: Final[str] = "mission_control_issue_intent_alignment"
ISSUE_INTENT_ALIGNMENT_ROUTE_ID: Final[str] = "mission_control_issue_intent_alignment"

ISSUE_INTENT_ALIGNMENT_INVARIANT: Final[str] = (
    "issue_intent_alignment_validates_issue_scope_and_patch_targets_before_patch_execution_without_patch_authority"
)

ALIGNMENT_ESCALATION_THRESHOLD: Final[int] = 80

TARGET_VALIDATION_STATUSES: Final[tuple[str, ...]] = (
    "aligned",
    "partially_aligned",
    "misaligned",
    "pre_patch",
    "indeterminate",
)

# Section keys owned by FIX 181 — FIX 184 must never emit these (composition only).
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

ISSUE_INTENT_ALIGNMENT_RECORD_KINDS: Final[tuple[str, ...]] = (
    "alignment_artifact",
    "alignment_review_acknowledged",
    "alignment_escalation_reviewed",
    "misalignment_note",
    "alignment_record",
)

UNRELATED_SUBSYSTEM_PREFIXES: Final[tuple[tuple[str, str], ...]] = (
    (".github/workflows/", "workflow_file"),
    ("aethos_core/governance/", "governance_file"),
    ("aethos_core/mission_control/", "mission_control_file"),
    ("aethos_core/providers/", "provider_integration_file"),
    ("web/lib/missionControl/", "mission_control_ui_file"),
)

ISSUE_INTENT_ALIGNMENT_PRINCIPLES: Final[tuple[tuple[str, str], ...]] = (
    ("validation_not_execution", "Alignment validation ≠ patch execution."),
    ("advisory_score", "Alignment score is advisory — it does not execute or block autonomously."),
    ("scope_before_patch", "Intent extraction and target validation occur before patch generation."),
    ("no_scope_expansion", "No implicit authorization envelope expansion."),
    ("unrelated_change_detection", "Unrelated workflow, governance, and provider files flagged."),
    ("human_reengagement_on_misalignment", "Operator re-engagement required when escalation triggers fire."),
    ("composes_upstream", "FIX 184 composes FIX 181 pilot harness context — never redefines pilot sections."),
)

FORBIDDEN_ALIGNMENT_ACTIONS: Final[tuple[tuple[str, str], ...]] = (
    ("patch_execution", "Alignment layer never executes patches."),
    ("autonomous_file_override", "Alignment layer never overrides file selection."),
    ("autonomous_scope_expansion", "Alignment layer never expands authorization envelope."),
    ("gate_bypass", "Alignment layer never bypasses governed gates."),
    ("hidden_patch_apply", "Alignment layer never applies workspace mutations."),
    ("direct_provider_mutation", "Alignment layer never mutates providers."),
)

ISSUE_INTENT_ALIGNMENT_EXECUTABLE: Final[bool] = False

MAX_ISSUE_INTENT_ALIGNMENT_CONTENT_LEN: Final[int] = 4000
MAX_PERSISTED_ISSUE_INTENT_ALIGNMENT_RECORDS: Final[int] = 500
