# SPDX-License-Identifier: Apache-2.0
"""Autonomous execution plane — task registry, plans, checkpoints, dispatcher."""

from aethos_core.autonomous_execution.plane_service import (
    dispatch_until_idle,
    plane_status_snapshot,
    submit_noop_task,
    submit_planned_task,
)

__all__ = [
    "dispatch_until_idle",
    "plane_status_snapshot",
    "submit_noop_task",
    "submit_planned_task",
]
