# SPDX-License-Identifier: Apache-2.0
"""Deployment target registry — config-driven deploy profiles."""

from aethos_core.deployment_targets.registry import (
    delete_target,
    find_target_by_alias,
    find_target_by_repo,
    get_target,
    list_targets,
    match_aliases_in_text,
    register_target,
    update_target,
)

__all__ = [
    "delete_target",
    "find_target_by_alias",
    "find_target_by_repo",
    "get_target",
    "list_targets",
    "match_aliases_in_text",
    "register_target",
    "update_target",
]
