# SPDX-License-Identifier: Apache-2.0
"""
FIX 126 — Frozen Phase 2 software delivery loop (machine-readable).

Import in certification tests to prevent silent drift of phase order,
route IDs, approval phrases, and lane boundaries before multi-agent roles (125J / 127).
"""

from __future__ import annotations

from typing import Final

from aethos_core.software_delivery.branch_orchestration_contract import (
    BRANCH_CREATE_APPROVAL_PHRASE,
)
from aethos_core.software_delivery.branch_push_contract import (
    BRANCH_PUSH_APPROVAL_PHRASE,
    MUTATION_PREVIEW_ACK_PHRASE,
)
from aethos_core.software_delivery.github_pr_open_contract import (
    GITHUB_PR_OPEN_APPROVAL_PHRASE,
)
from aethos_core.software_delivery.github_pr_preflight_contract import (
    GITHUB_PR_PREFLIGHT_APPROVAL_PHRASE,
)
from aethos_core.software_delivery.issue_plan_contract import (
    PLANNING_APPROVAL_PHRASE,
    SOFTWARE_DELIVERY_LANE_ID,
)
from aethos_core.software_delivery.patch_proposal_contract import (
    PATCH_PROPOSAL_APPROVAL_PHRASE,
)
from aethos_core.software_delivery.workspace_application_contract import (
    WORKSPACE_APPLY_APPROVAL_PHRASE,
    WORKSPACE_ROLLBACK_APPROVAL_PHRASE,
)

SOFTWARE_DELIVERY_FIX_RANGE: Final[str] = "FIX 125A–FIX 125I"
SOFTWARE_DELIVERY_PHASE_2_FREEZE_FIX: Final[str] = "FIX 126"
SOFTWARE_DELIVERY_PHASE_2_SCHEMA_VERSION: Final[str] = "software_delivery_phase_2_v2"
SOFTWARE_DELIVERY_PHASE_2_FROZEN: Final[bool] = True

# Certification baselines (make certify must stay at or above these).
SOFTWARE_DELIVERY_MIN_CERT_MODULES: Final[int] = 19
SOFTWARE_DELIVERY_MIN_TEST_COUNT: Final[int] = 61

# Git commit that introduced this freeze contract revision (update on re-freeze only).
SOFTWARE_DELIVERY_FROZEN_COMMIT_REF: Final[str] = "3dfa0f9"

SOFTWARE_DELIVERY_FROZEN_LANES: Final[tuple[str, ...]] = (
    "issue_planning",
    "branch_orchestration",
    "patch_proposal",
    "workspace_apply",
    "workspace_verification",
    "pr_drafting",
    "github_pr_preflight",
    "governed_branch_push",
    "governed_pr_open",
)

SOFTWARE_DELIVERY_LANE_OWNERSHIP_MAP: Final[dict[str, str]] = {
    "issue_planning": "aethos_core.software_delivery.issue_plan_service",
    "branch_orchestration": "aethos_core.software_delivery.branch_orchestration_service",
    "patch_proposal": "aethos_core.software_delivery.patch_proposal_service",
    "workspace_apply": "aethos_core.software_delivery.workspace_application_service",
    "workspace_verification": "aethos_core.software_delivery.workspace_verification_service",
    "pr_drafting": "aethos_core.software_delivery.pr_draft_service",
    "github_pr_preflight": "aethos_core.software_delivery.github_pr_preflight_service",
    "governed_branch_push": "aethos_core.software_delivery.branch_push_service",
    "governed_pr_open": "aethos_core.software_delivery.github_pr_open_service",
    "unified_router": "aethos_core.software_delivery.software_delivery_router",
}

SOFTWARE_DELIVERY_FROZEN_INVARIANTS: Final[tuple[str, ...]] = (
    "governed_workspace_only",
    "no_repo_mutation_outside_approved_stages",
    "no_merge",
    "no_deploy",
    "no_railway_coupling",
    "human_review_mandatory",
    "exact_approval_phrases_required",
    "receipts_and_timelines_mandatory",
    "idempotency_mandatory",
    "rollback_snapshots_mandatory",
    "software_delivery_lane_not_infrastructure_lane",
)

SOFTWARE_DELIVERY_FORBIDDEN_CAPABILITIES: Final[tuple[str, ...]] = (
    "auto_merge",
    "deploy",
    "railway_mutation",
    "production_deploy",
    "arbitrary_shell_execution",
    "unrestricted_file_mutation",
    "dependency_installation",
    "autonomous_pr_approval",
    "autonomous_rollout_promotion",
    "autonomous_rollback",
    "multi_agent_concurrent_mutation",
    "self_authorizing_execution",
)

# Terminal loop through human-review PR (125J+ requires explicit sign-off).
SOFTWARE_DELIVERY_LOOP_ORDER: Final[tuple[str, ...]] = (
    "issue_intake",
    "implementation_plan",
    "implementation_branch",
    "patch_proposal",
    "workspace_apply",
    "workspace_verify",
    "pr_draft",
    "github_pr_preflight",
    "branch_push",
    "pr_open",
    "human_review",
)

SOFTWARE_DELIVERY_LOOP_FIX_MAP: Final[dict[str, str]] = {
    "issue_intake": "FIX 125A",
    "implementation_plan": "FIX 125A",
    "implementation_branch": "FIX 125B",
    "patch_proposal": "FIX 125C",
    "workspace_apply": "FIX 125D",
    "workspace_verify": "FIX 125E",
    "pr_draft": "FIX 125F",
    "github_pr_preflight": "FIX 125G",
    "branch_push": "FIX 125H",
    "pr_open": "FIX 125I",
    "human_review": "operator",
}

SOFTWARE_DELIVERY_SHIPPED_FIXES: Final[tuple[str, ...]] = (
    "FIX 125A",
    "FIX 125B",
    "FIX 125C",
    "FIX 125D",
    "FIX 125E",
    "FIX 125F",
    "FIX 125G",
    "FIX 125H",
    "FIX 125I",
)

SOFTWARE_DELIVERY_ROUTE_ID: Final[str] = SOFTWARE_DELIVERY_LANE_ID

SOFTWARE_DELIVERY_CERTIFIED_STAGES: Final[frozenset[str]] = frozenset(
    {
        "patch_propose_files",
        "patch_intent",
        "patch_diff_preview",
        "patch_approve",
        "patch_status",
        "workspace_apply",
        "workspace_rollback",
        "workspace_diff",
        "workspace_status",
        "workspace_verify_run",
        "workspace_verify_report",
        "workspace_verify_status",
        "pr_draft_create",
        "pr_draft_show",
        "github_pr_preflight_run",
        "github_pr_preflight_approve",
        "github_pr_preflight_show",
        "github_branch_push",
        "github_branch_push_show",
        "github_pr_open",
        "github_pr_open_show",
        "branch_create",
        "branch_archive",
        "branch_restore",
        "timeline",
        "branch_status",
    }
)

SOFTWARE_DELIVERY_APPROVAL_PHRASES: Final[tuple[str, ...]] = (
    PLANNING_APPROVAL_PHRASE,
    BRANCH_CREATE_APPROVAL_PHRASE,
    PATCH_PROPOSAL_APPROVAL_PHRASE,
    WORKSPACE_APPLY_APPROVAL_PHRASE,
    WORKSPACE_ROLLBACK_APPROVAL_PHRASE,
    GITHUB_PR_PREFLIGHT_APPROVAL_PHRASE,
    BRANCH_PUSH_APPROVAL_PHRASE,
    MUTATION_PREVIEW_ACK_PHRASE,
    GITHUB_PR_OPEN_APPROVAL_PHRASE,
)

SOFTWARE_DELIVERY_MERGE_ENABLED: Final[bool] = False
SOFTWARE_DELIVERY_DEPLOY_ENABLED: Final[bool] = False
SOFTWARE_DELIVERY_RAILWAY_MUTATION_ENABLED: Final[bool] = False
SOFTWARE_DELIVERY_AUTO_REVIEW_APPROVAL_ENABLED: Final[bool] = False

SOFTWARE_DELIVERY_DEFERRED_AFTER_FREEZE: Final[tuple[str, ...]] = (
    "executor_agent_autonomous_mutation",
    "expanded_parallel_agent_orchestration",
    "review_agents",
    "repo_graph_intelligence",
    "parallel_planning",
    "autonomous_issue_batching",
    "mission_orchestration",
    "governed_merge_flows",
    "governed_deployment_promotion",
)

SOFTWARE_DELIVERY_LANE_DOC_PATHS: Final[tuple[str, ...]] = (
    "docs/SOFTWARE_DELIVERY_PHASE_2_INDEX.md",
    "docs/SOFTWARE_DELIVERY_ISSUE_PLAN_LANE.md",
    "docs/SOFTWARE_DELIVERY_BRANCH_ORCHESTRATION_LANE.md",
    "docs/SOFTWARE_DELIVERY_PATCH_PROPOSAL_LANE.md",
    "docs/SOFTWARE_DELIVERY_WORKSPACE_APPLICATION_LANE.md",
    "docs/SOFTWARE_DELIVERY_WORKSPACE_VERIFICATION_LANE.md",
    "docs/SOFTWARE_DELIVERY_PR_DRAFT_LANE.md",
    "docs/SOFTWARE_DELIVERY_GITHUB_PR_PREFLIGHT_LANE.md",
    "docs/SOFTWARE_DELIVERY_BRANCH_PUSH_LANE.md",
    "docs/SOFTWARE_DELIVERY_GITHUB_PR_OPEN_LANE.md",
    "docs/SOFTWARE_DELIVERY_PHASE_2_CERTIFICATION_FREEZE.md",
    "docs/SOFTWARE_DELIVERY_PHASE_2_OPERATOR_RUNBOOK.md",
    "docs/SOFTWARE_DELIVERY_MULTI_AGENT_LANE.md",
)

assert len(SOFTWARE_DELIVERY_LOOP_ORDER) == 11
assert SOFTWARE_DELIVERY_LOOP_ORDER[-1] == "human_review"
assert SOFTWARE_DELIVERY_PHASE_2_FROZEN is True
assert len(SOFTWARE_DELIVERY_FROZEN_LANES) == 9
