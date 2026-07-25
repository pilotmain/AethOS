# SPDX-License-Identifier: Apache-2.0
"""FIX 187 — independent repository trust expansion contract."""

from __future__ import annotations

from typing import Final

INDEPENDENT_REPOSITORY_TRUST_EXPANSION_SCHEMA_VERSION: Final[str] = (
    "mission_control_independent_repository_trust_expansion_v1"
)
INDEPENDENT_REPOSITORY_TRUST_EXPANSION_RECORD_SCHEMA_VERSION: Final[str] = (
    "mission_control_independent_repository_trust_expansion_record_v1"
)
INDEPENDENT_REPOSITORY_TRUST_EXPANSION_FIX: Final[str] = "FIX 187"

MUTATION_PERFORMED_FIX_187: Final[bool] = False
EXECUTION_PERFORMED_FIX_187: Final[bool] = False
DIRECT_EXECUTION_PERFORMED_FIX_187: Final[bool] = False
DIRECT_PROVIDER_MUTATION_PERFORMED_FIX_187: Final[bool] = False
PILOT_EXECUTION_PERFORMED_FIX_187: Final[bool] = False
AUTONOMOUS_TRUST_EXPANSION_ENABLED_FIX_187: Final[bool] = False
HIDDEN_PILOT_EXECUTION_PERFORMED_FIX_187: Final[bool] = False
GATE_BYPASS_ENABLED_FIX_187: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_187: Final[bool] = False

TRUST_TRANSFER_ENABLED_FIX_187: Final[bool] = False
AUTOMATIC_REPO_TRUST_INHERITANCE_ENABLED_FIX_187: Final[bool] = False
CROSS_REPO_AUTHORITY_ENABLED_FIX_187: Final[bool] = False

TRUST_EXPANSION_COMPOSES_ARTIFACTS_ONLY_FIX_187: Final[bool] = True
INDEPENDENT_REPOSITORY_TRUST_EXPANSION_ORIGIN: Final[str] = (
    "mission_control_independent_repository_trust_expansion"
)
INDEPENDENT_REPOSITORY_TRUST_EXPANSION_ROUTE_ID: Final[str] = (
    "mission_control_independent_repository_trust_expansion"
)

INDEPENDENT_REPOSITORY_TRUST_EXPANSION_INVARIANT: Final[str] = (
    "independent_repository_trust_expansion_composes_fix_186_and_per_repo_pilot_evidence_without_trust_transfer_or_pilot_execution"
)

TRUST_STATES: Final[tuple[str, ...]] = (
    "UNPROVEN",
    "PILOTING",
    "CONDITIONALLY_TRUSTED",
    "EXPANDED_TRUST",
)

PILOT_TRUST_STAGES: Final[tuple[tuple[str, str], ...]] = (
    ("stage_1", "Loop completion"),
    ("stage_2", "Intent alignment protection"),
    ("stage_3", "Correct content generation"),
    ("stage_4", "Trust freeze"),
)

PHASE_1_REPOSITORY: Final[str] = "pilotmain/AethOS"
PHASE_2_REPOSITORY_ORDER: Final[tuple[str, ...]] = (
    "pilotmain/pilot-os-ui",
    "pilotmain/atlas-trader",
    "pilotmain/nexora-monorepo-starter",
)

ALL_REGISTRY_REPOSITORIES: Final[tuple[str, ...]] = (PHASE_1_REPOSITORY, *PHASE_2_REPOSITORY_ORDER)

EXPANSION_REQUIREMENTS: Final[tuple[str, ...]] = (
    "fix_186_trust_report_freeze_reviewed",
    "operator_expansion_approval_recorded",
    "fix_182_readiness_passes",
    "repository_specific_issue_selected",
    "scope_bounded",
    "blast_radius_low",
)

INDEPENDENT_REPOSITORY_TRUST_EXPANSION_RECORD_KINDS: Final[tuple[str, ...]] = (
    "repo_expansion_approval",
    "repo_pilot_evidence_note",
    "trust_registry_note",
    "sequence_skip_approval",
    "repository_trust_record",
)

INDEPENDENT_REPOSITORY_TRUST_EXPANSION_PRINCIPLES: Final[tuple[tuple[str, str], ...]] = (
    ("trust_non_transferable", "Repository trust is non-transferable — success on A does not imply trust on B."),
    ("independent_evidence", "Each repository earns trust through its own pilot evidence arc."),
    ("expansion_not_execution", "Trust expansion contract ≠ pilot execution."),
    ("no_inherited_trust", "No automatic cross-repo trust inheritance."),
    ("sequenced_expansion", "Phase 2 repos follow ordered expansion with explicit skip approval."),
    ("fix_186_prerequisite", "FIX 186 trust report freeze must be reviewed before Phase 2 pilot entry."),
    ("fix_182_prerequisite", "FIX 182 readiness must pass before repository pilot execution."),
    ("four_stage_progression", "Each repo independently demonstrates stages 1–4 before conditional trust."),
)

FORBIDDEN_TRUST_EXPANSION_ACTIONS: Final[tuple[tuple[str, str], ...]] = (
    ("trust_transfer", "Trust expansion never transfers trust between repositories."),
    ("automatic_inheritance", "Trust expansion never auto-grants inherited repo trust."),
    ("cross_repo_authority", "Trust expansion never grants cross-repo execution authority."),
    ("pilot_execution", "Trust expansion contract never runs pilot harness."),
    ("pilot_reexecution", "Trust expansion contract never re-runs completed pilots."),
    ("direct_provider_mutation", "Trust expansion contract never mutates providers."),
    ("gate_bypass", "Trust expansion contract never bypasses frozen gates."),
    ("sequence_skip_without_approval", "Repositories may not skip expansion order without operator approval."),
    ("merge", "Trust expansion contract never merges pull requests."),
    ("deploy", "Trust expansion contract never deploys."),
    ("railway_mutation", "Trust expansion contract never mutates Railway infrastructure."),
)

INDEPENDENT_REPOSITORY_TRUST_EXPANSION_EXECUTABLE: Final[bool] = False

MAX_INDEPENDENT_REPOSITORY_TRUST_EXPANSION_CONTENT_LEN: Final[int] = 4000
MAX_PERSISTED_INDEPENDENT_REPOSITORY_TRUST_EXPANSION_RECORDS: Final[int] = 500

UPSTREAM_SECTIONS_OWNED_BY_FIX_186: Final[tuple[str, ...]] = (
    "frozen_evidence_timeline",
    "pilot_artifact_composition",
    "fix_183_metrics_composition",
    "trust_boundary_matrix",
    "dogfood_trust_recommendation",
    "expansion_recommendation",
    "evidence_index",
    "scaling_gate",
)
