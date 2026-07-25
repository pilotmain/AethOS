# SPDX-License-Identifier: Apache-2.0
"""Mutation job taxonomy — canonical lifecycle types."""

from __future__ import annotations

CANONICAL_MUTATION_PREFLIGHT_JOB_TYPE = "mutation_preflight"
CANONICAL_MUTATION_EXECUTION_JOB_TYPE = "mutation_execution"

MUTATION_OPERATION_TYPES = frozenset(
    {
        "redeploy",
        "restart",
        "stop",
        "set_env_var",
        "deploy_from_git",
        "local_commit_preflight",
        "local_push_preflight",
        "git_deploy_preflight",
        "workflow_rerun",
        "social_post",
    }
)

MUTATION_PREFLIGHT_JOB_TYPES = frozenset({CANONICAL_MUTATION_PREFLIGHT_JOB_TYPE})
MUTATION_EXECUTION_JOB_TYPES = frozenset({CANONICAL_MUTATION_EXECUTION_JOB_TYPE})


def is_mutation_operation(operation_type: str | None) -> bool:
    if not operation_type:
        return False
    return operation_type in MUTATION_OPERATION_TYPES
