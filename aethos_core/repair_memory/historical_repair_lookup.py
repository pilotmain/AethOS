# SPDX-License-Identifier: Apache-2.0
"""Historical repair attempt lookup."""

from __future__ import annotations

from aethos_core.repair_memory.repair_attempt_memory import (
    RepairAttemptOutcome,
    list_repair_attempts,
    lookup_latest_for_service,
    lookup_latest_for_target,
)

__all__ = [
    "RepairAttemptOutcome",
    "list_repair_attempts",
    "lookup_latest_for_service",
    "lookup_latest_for_target",
    "lookup_latest_failed_restart",
    "should_avoid_repeat_restart",
]


def lookup_latest_failed_restart(
    *,
    target_path: str | None = None,
    service: str | None = None,
    operation: str = "restart",
) -> RepairAttemptOutcome | None:
    if target_path:
        latest = lookup_latest_for_target(target_path, operation=operation)
        if latest is not None and not latest.helped:
            return latest
    if service:
        latest = lookup_latest_for_service(service, operation=operation)
        if latest is not None and not latest.helped:
            return latest
    for row in list_repair_attempts(limit=20):
        if row.operation.lower() != operation.lower():
            continue
        if row.helped:
            continue
        if target_path and row.target.lower() != target_path.strip().lower():
            continue
        if service and row.service.lower() != service.strip().lower():
            continue
        if row.result in {"regressed", "failed_after_mutation"}:
            return row
    return None


def should_avoid_repeat_restart(
    *,
    target_path: str | None = None,
    service: str | None = None,
    operation: str = "restart",
) -> bool:
    return lookup_latest_failed_restart(
        target_path=target_path,
        service=service,
        operation=operation,
    ) is not None
