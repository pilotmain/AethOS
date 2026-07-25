# SPDX-License-Identifier: Apache-2.0
"""FIX 125B — governed branch orchestration contract."""

from __future__ import annotations

from typing import Final, Literal

BranchLifecycleState = Literal["not_created", "active", "archived", "restored"]

BRANCH_ORCHESTRATION_SCHEMA_VERSION: Final[str] = "software_delivery_branch_v1"
BRANCH_ORCHESTRATION_FIX: Final[str] = "FIX 125B"

BRANCH_CREATE_APPROVAL_PHRASE: Final[str] = (
    "I authorize creating the governed implementation branch for this software delivery plan."
)
BRANCH_ARCHIVE_APPROVAL_PHRASE: Final[str] = (
    "I authorize archiving the governed implementation branch for this software delivery plan."
)
BRANCH_RESTORE_APPROVAL_PHRASE: Final[str] = (
    "I authorize restoring the governed implementation branch for this software delivery plan."
)

CODE_MODIFICATION_ENABLED_FIX_125B: Final[bool] = False
PR_CREATION_ENABLED_FIX_125B: Final[bool] = False
MERGE_ENABLED_FIX_125B: Final[bool] = False

BRANCH_RECEIPT_PHASES: Final[tuple[str, ...]] = (
    "branch_context_created",
    "workspace_isolated",
    "branch_create_simulated",
    "branch_archived",
    "branch_restored",
)
