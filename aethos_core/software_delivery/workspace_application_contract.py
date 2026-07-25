# SPDX-License-Identifier: Apache-2.0
"""FIX 125D — governed workspace code application contract."""

from __future__ import annotations

from typing import Final

WORKSPACE_APPLICATION_SCHEMA_VERSION: Final[str] = "software_delivery_workspace_apply_v1"
WORKSPACE_APPLICATION_FIX: Final[str] = "FIX 125D"

WORKSPACE_APPLY_APPROVAL_PHRASE: Final[str] = (
    "I authorize applying the approved patch proposal to the governed software delivery workspace."
)
WORKSPACE_ROLLBACK_APPROVAL_PHRASE: Final[str] = (
    "I authorize rolling back the governed software delivery workspace to the pre-apply snapshot."
)

GIT_COMMIT_ENABLED_FIX_125D: Final[bool] = False
PR_CREATION_ENABLED_FIX_125D: Final[bool] = False
MERGE_ENABLED_FIX_125D: Final[bool] = False
DEPLOY_ENABLED_FIX_125D: Final[bool] = False
INFRA_MUTATION_ENABLED_FIX_125D: Final[bool] = False
SHELL_EXECUTION_ENABLED_FIX_125D: Final[bool] = False
DEPENDENCY_INSTALL_ENABLED_FIX_125D: Final[bool] = False
REPO_WRITE_ENABLED_FIX_125D: Final[bool] = False

WORKSPACE_APPLY_RECEIPT_PHASES: Final[tuple[str, ...]] = (
    "proposal_and_workspace_validated",
    "rollback_snapshot_created",
    "patch_applied_to_workspace",
    "workspace_diff_recorded",
    "workspace_apply_completed",
    "workspace_rollback_completed",
)
