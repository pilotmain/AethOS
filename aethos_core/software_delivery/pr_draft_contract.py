# SPDX-License-Identifier: Apache-2.0
"""FIX 125F — governed PR draft artifact contract (no GitHub PR yet)."""

from __future__ import annotations

from typing import Final

PR_DRAFT_SCHEMA_VERSION: Final[str] = "software_delivery_pr_draft_v1"
PR_DRAFT_FIX: Final[str] = "FIX 125F"

GITHUB_PR_CREATION_ENABLED_FIX_125F: Final[bool] = False
GIT_PUSH_ENABLED_FIX_125F: Final[bool] = False
GIT_COMMIT_ENABLED_FIX_125F: Final[bool] = False
MERGE_ENABLED_FIX_125F: Final[bool] = False
DEPLOY_ENABLED_FIX_125F: Final[bool] = False
REPO_WRITE_ENABLED_FIX_125F: Final[bool] = False

PR_DRAFT_RECEIPT_PHASES: Final[tuple[str, ...]] = (
    "verification_gate_passed",
    "pr_draft_composed",
    "pr_draft_persisted",
)

HUMAN_REVIEW_REQUIREMENTS: Final[tuple[str, ...]] = (
    "Human reviewer must confirm workspace verification passed",
    "Human reviewer must read governed workspace diff vs repo",
    "Human must merge — no auto-merge from software delivery lane",
    "Human must approve any production deploy separately (infra lane)",
    "GitHub PR creation requires FIX 125G explicit step",
)
