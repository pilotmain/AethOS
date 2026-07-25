# SPDX-License-Identifier: Apache-2.0
"""FIX 125C — bounded patch proposal contract (no file writes)."""

from __future__ import annotations

from typing import Final

PATCH_PROPOSAL_SCHEMA_VERSION: Final[str] = "software_delivery_patch_proposal_v1"
PATCH_PROPOSAL_FIX: Final[str] = "FIX 125C"

PATCH_PROPOSAL_APPROVAL_PHRASE: Final[str] = (
    "I approve this governed software delivery patch proposal for bounded application."
)

FILE_WRITE_ENABLED_FIX_125C: Final[bool] = False
GIT_COMMIT_ENABLED_FIX_125C: Final[bool] = False
PR_CREATION_ENABLED_FIX_125C: Final[bool] = False
MERGE_ENABLED_FIX_125C: Final[bool] = False
DEPLOY_ENABLED_FIX_125C: Final[bool] = False

PATCH_RECEIPT_PHASES: Final[tuple[str, ...]] = (
    "plan_and_branch_inspected",
    "patch_files_proposed",
    "patch_intent_generated",
    "diff_preview_recorded",
    "patch_proposal_approved",
)
