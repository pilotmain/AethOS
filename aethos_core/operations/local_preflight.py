# SPDX-License-Identifier: Apache-2.0
"""Local workspace operation preflight — read-only planning; execution gated by phase."""

from __future__ import annotations

from aethos_core.operations.operation_models import OperationPreflight
from aethos_core.runtime.workspace_diagnostics import resolve_workspace_root


def build_local_preflight(*, operation_type: str, user_request: str) -> OperationPreflight:
    root = resolve_workspace_root()
    root_str = str(root)

    steps = [
        "Read-only: `git status` and current branch.",
        "Read-only: inspect package scripts and test commands.",
        "Read-only: run tests/typecheck/lint when approved in a later phase.",
        "Summarize findings before any code changes.",
    ]
    if operation_type == "local_commit_preflight":
        steps.append("Prepare commit proposal — mutating execution remains disabled in Phase 9.3B.")
    if operation_type == "local_push_preflight":
        steps.append("Prepare push proposal — mutating execution remains disabled in Phase 9.3B.")
    if operation_type == "git_deploy_preflight":
        steps.append("Prepare deploy proposal — mutating execution remains disabled in Phase 9.3B.")

    return OperationPreflight(
        provider="local",
        operation_type=operation_type,
        target_name=root_str,
        target_status="resolved",
        risk_level="medium",
        mutation_required=True,
        required_approval=True,
        current_state={
            "scope": "local_repository",
            "repo_path": root_str,
            "workspace_root": root_str,
        },
        proposed_steps=steps,
        blockers=["Phase 9.3B: local command execution for fixes is not enabled yet."],
        missing_information=[],
        next_action="approval_required_before_execution",
    )
