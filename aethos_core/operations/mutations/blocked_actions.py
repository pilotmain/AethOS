# SPDX-License-Identifier: Apache-2.0
"""Hard-blocked mutation actions until governed execution is enabled."""

from __future__ import annotations

HARD_BLOCKED_OPERATIONS = frozenset(
    {
        "delete_resource",
        "force_push",
        "branch_delete",
        "merge_production",
        "bulk_env_overwrite",
        "domain_delete",
        "credential_rotation",
        "autonomous_post",
        "stealth_post",
    }
)


def is_hard_blocked(operation_type: str) -> bool:
    return operation_type in HARD_BLOCKED_OPERATIONS


def block_reason(operation_type: str) -> str:
    return f"Operation `{operation_type}` is hard-blocked until governed mutation execution is enabled."
