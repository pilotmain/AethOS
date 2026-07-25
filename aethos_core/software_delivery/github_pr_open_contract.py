# SPDX-License-Identifier: Apache-2.0
"""FIX 125I — governed GitHub PR open contract (PR create only)."""

from __future__ import annotations

from typing import Final

GITHUB_PR_OPEN_SCHEMA_VERSION: Final[str] = "software_delivery_github_pr_open_v1"
GITHUB_PR_OPEN_FIX: Final[str] = "FIX 125I"

GITHUB_PR_OPEN_APPROVAL_PHRASE: Final[str] = (
    "I authorize opening the governed GitHub pull request for human review."
)

MERGE_ENABLED_FIX_125I: Final[bool] = False
DEPLOY_ENABLED_FIX_125I: Final[bool] = False
RAILWAY_MUTATION_ENABLED_FIX_125I: Final[bool] = False
AUTO_REVIEW_APPROVAL_ENABLED_FIX_125I: Final[bool] = False
HUMAN_REVIEW_REQUIRED_FIX_125I: Final[bool] = True

GITHUB_PR_OPEN_RECEIPT_PHASES: Final[tuple[str, ...]] = (
    "pr_open_gates_validated",
    "pull_request_opened",
    "pr_url_persisted",
    "pr_open_completed",
)
