# SPDX-License-Identifier: Apache-2.0
"""FIX 185 — issue intake scope fidelity contract."""

from __future__ import annotations

from typing import Final

ISSUE_INTAKE_SCOPE_FIDELITY_FIX: Final[str] = "FIX 185"
ISSUE_INTAKE_SCOPE_FIDELITY_SCHEMA_VERSION: Final[str] = "issue_intake_scope_fidelity_v1"

INTAKE_FIDELITY_PERFORMED_FIX_185: Final[bool] = True
PLAN_AUTHORITY_ENABLED_FIX_185: Final[bool] = False
AUTONOMOUS_SCOPE_EXPANSION_ENABLED_FIX_185: Final[bool] = False
AUTONOMOUS_PLAN_GOAL_OVERRIDE_ENABLED_FIX_185: Final[bool] = False

ISSUE_INTAKE_SCOPE_FIDELITY_INVARIANT: Final[str] = (
    "issue_intake_scope_fidelity_preserves_github_issue_scope_without_plan_authority_or_autonomous_reframing"
)

FIDELITY_ESCALATION_THRESHOLD: Final[int] = 80

FORBIDDEN_OUT_OF_SCOPE_PREFIXES: Final[tuple[tuple[str, str], ...]] = (
    (".github/workflows/", "workflow_file"),
    ("aethos_core/providers/", "provider_integration_file"),
    ("aethos_core/operations/mutations/", "mutation_file"),
    ("aethos_core/governance/", "governance_file"),
)

FORBIDDEN_OUT_OF_SCOPE_KEYWORDS: Final[tuple[str, ...]] = (
    "workflow files",
    "provider files",
    "mutation files",
    "railway",
    "deploy",
    "merge",
)

WORKFLOW_REFRAME_GOAL_RX: Final[str] = r"fix github workflow rerun resolution"

ISSUE_INTAKE_SCOPE_FIDELITY_PRINCIPLES: Final[tuple[tuple[str, str], ...]] = (
    ("fidelity_not_plan_authority", "Issue intake fidelity ≠ plan authority."),
    ("live_issue_source", "Scope extracted from live GitHub issue title/body."),
    ("explicit_paths", "Expected file paths extracted from issue-authored scope."),
    ("out_of_scope_preserved", "Out-of-scope constraints preserved from issue body."),
    ("no_stale_reframe", "Heuristic workflow/railway templates must not override explicit issue scope."),
    ("plan_goal_comparison", "Generated plan goal compared against issue scope before downstream planning."),
    ("feeds_fix_184", "Fidelity envelope feeds FIX 184 expected targets."),
)

FIX_185_CERTIFICATION_REQUIREMENTS: Final[tuple[str, ...]] = (
    "issue_intake_scope_fidelity_extracts_expected_files_from_github_issue_body",
    "issue_intake_scope_fidelity_preserves_out_of_scope_constraints",
    "plan_goal_divergence_from_issue_scope_detected_before_planning_approval",
    "workflow_heuristic_reframe_blocked_when_issue_has_explicit_bounded_scope",
    "issue_intake_scope_fidelity_feeds_fix_184_expected_targets",
    "no_autonomous_plan_authority_or_scope_expansion_from_intake_fidelity_layer",
    "dogfood_issue_1_produces_doc_scoped_plan_not_workflow_reframe",
)