# SPDX-License-Identifier: Apache-2.0
"""Proactive automation scheduler — re-export for API lifespan wiring."""

from aethos_core.automation.scheduler import (
    reset_scheduler_state_for_tests,
    run_due_scheduled_tasks,
    scheduler_status,
    start_automation_scheduler,
    stop_automation_scheduler,
)

__all__ = [
    "reset_scheduler_state_for_tests",
    "run_due_scheduled_tasks",
    "scheduler_status",
    "start_automation_scheduler",
    "stop_automation_scheduler",
]
