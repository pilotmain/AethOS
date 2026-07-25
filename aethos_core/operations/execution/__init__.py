# SPDX-License-Identifier: Apache-2.0
"""Approved read-only execution — Phase 9.3."""

from aethos_core.operations.execution.execution_permissions import (
    READONLY_ACTIONS,
    is_mutating_operation,
)

__all__ = ["READONLY_ACTIONS", "is_mutating_operation"]
