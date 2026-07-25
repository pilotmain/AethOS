# SPDX-License-Identifier: Apache-2.0
"""FIX 125G — GitHub PR creation preflight contract (no GitHub mutation)."""

from __future__ import annotations

from typing import Final

GITHUB_PR_PREFLIGHT_SCHEMA_VERSION: Final[str] = "software_delivery_github_pr_preflight_v1"
GITHUB_PR_PREFLIGHT_FIX: Final[str] = "FIX 125G"

GITHUB_PR_PREFLIGHT_APPROVAL_PHRASE: Final[str] = (
    "I authorize proceeding with governed GitHub PR creation after this preflight."
)

# Mutations deferred to 125H / 125I
GIT_PUSH_ENABLED_FIX_125G: Final[bool] = False
GITHUB_PR_CREATE_ENABLED_FIX_125G: Final[bool] = False
REPO_WRITE_ENABLED_FIX_125G: Final[bool] = False
MERGE_ENABLED_FIX_125G: Final[bool] = False
DEPLOY_ENABLED_FIX_125G: Final[bool] = False

MAX_PACKAGE_BYTES_FIX_125G: Final[int] = 512_000
MAX_PACKAGE_FILES_FIX_125G: Final[int] = 24

PREFLIGHT_RECEIPT_PHASES: Final[tuple[str, ...]] = (
    "readiness_gate_evaluated",
    "github_auth_scope_checked",
    "branch_push_readiness_assessed",
    "diff_package_measured",
    "protected_branch_policy_reviewed",
    "mutation_preview_recorded",
    "preflight_completed",
    "preflight_approved",
)
