# SPDX-License-Identifier: Apache-2.0
"""Execution step results — structured outcomes from provider tools."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

StepStatus = Literal["completed", "blocked", "skipped", "awaiting_approval", "failed"]


@dataclass
class ExecutionStepResult:
    step_id: str
    label: str
    status: StepStatus
    detail: str = ""
    blocker_code: str = ""
    evidence: dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionPlanResult:
    goal_summary: str
    provider: str
    steps: list[ExecutionStepResult] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    next_executable_step: str = ""
    awaiting_approval: bool = False
    job_id: str = ""
    checks_snapshot: dict[str, Any] = field(default_factory=dict)
    recovery_summary: str = ""
    completion_ready: bool = False

    @property
    def completed_count(self) -> int:
        return sum(1 for step in self.steps if step.status == "completed")

    @property
    def blocked(self) -> bool:
        return any(step.status in {"blocked", "failed"} for step in self.steps)
