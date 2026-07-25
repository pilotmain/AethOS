# SPDX-License-Identifier: Apache-2.0
"""FIX 125H — governed GitHub branch push + commit contract."""

from __future__ import annotations

from typing import Final

BRANCH_PUSH_SCHEMA_VERSION: Final[str] = "software_delivery_branch_push_v1"
BRANCH_PUSH_FIX: Final[str] = "FIX 125H"

BRANCH_PUSH_APPROVAL_PHRASE: Final[str] = (
    "I authorize pushing the governed workspace changes to the GitHub feature branch."
)
MUTATION_PREVIEW_ACK_PHRASE: Final[str] = (
    "I acknowledge the governed branch push mutation preview from FIX 125G."
)

GITHUB_PR_CREATE_ENABLED_FIX_125H: Final[bool] = False
MERGE_ENABLED_FIX_125H: Final[bool] = False
DEPLOY_ENABLED_FIX_125H: Final[bool] = False
DIRECT_MAIN_PUSH_ENABLED_FIX_125H: Final[bool] = False

PROTECTED_DEFAULT_BRANCHES: Final[frozenset[str]] = frozenset({"main", "master"})

BRANCH_PUSH_RECEIPT_PHASES: Final[tuple[str, ...]] = (
    "push_gates_validated",
    "github_scope_rechecked",
    "feature_branch_created",
    "workspace_committed",
    "feature_branch_pushed",
    "push_completed",
)
