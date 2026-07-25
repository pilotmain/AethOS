# SPDX-License-Identifier: Apache-2.0
"""Execution lifecycle status."""

from __future__ import annotations

EXECUTION_STATUSES = frozenset(
    {
        "approved",
        "started",
        "running",
        "completed",
        "failed",
        "cancelled",
    }
)


def status_label(status: str) -> str:
    return {
        "approved": "Approved",
        "started": "Started",
        "running": "Running",
        "completed": "Completed",
        "failed": "Failed",
        "cancelled": "Cancelled",
    }.get(status, status.replace("_", " "))
