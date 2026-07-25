# SPDX-License-Identifier: Apache-2.0
"""FIX 125E — governed workspace verification contract."""

from __future__ import annotations

from typing import Final

WORKSPACE_VERIFICATION_SCHEMA_VERSION: Final[str] = "software_delivery_workspace_verify_v1"
WORKSPACE_VERIFICATION_FIX: Final[str] = "FIX 125E"

PR_DRAFTING_REQUIRES_VERIFICATION_FIX_125E: Final[bool] = True

GIT_COMMIT_ENABLED_FIX_125E: Final[bool] = False
PR_CREATION_ENABLED_FIX_125E: Final[bool] = False
MERGE_ENABLED_FIX_125E: Final[bool] = False
DEPLOY_ENABLED_FIX_125E: Final[bool] = False
REPO_WRITE_ENABLED_FIX_125E: Final[bool] = False
DEPENDENCY_INSTALL_ENABLED_FIX_125E: Final[bool] = False
ARBITRARY_SHELL_ENABLED_FIX_125E: Final[bool] = False

VERIFICATION_RECEIPT_PHASES: Final[tuple[str, ...]] = (
    "workspace_tree_inspected",
    "file_existence_verified",
    "static_diff_validated",
    "syntax_check_completed",
    "allowlisted_test_completed",
    "verification_classified",
    "verification_completed",
)

FAILURE_CLASSES: Final[tuple[str, ...]] = (
    "missing_workspace_file",
    "invalid_diff",
    "syntax_error",
    "allowlisted_test_failed",
    "verification_blocked",
    "unknown",
)

# Frozen argv only — no arbitrary shell.
ALLOWLISTED_TEST_COMMAND_KEY: Final[str] = "pytest_software_delivery_smoke"
ALLOWLISTED_TEST_COMMAND: Final[tuple[str, ...]] = (
    "python",
    "-m",
    "pytest",
    "tests/test_software_delivery_issue_plan.py",
    "tests/test_software_delivery_branch_orchestration.py",
    "tests/test_software_delivery_patch_proposal.py",
    "tests/test_software_delivery_workspace_application.py",
    "-q",
    "--tb=no",
    "--maxfail=1",
)
