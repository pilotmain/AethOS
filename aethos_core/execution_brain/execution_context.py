# SPDX-License-Identifier: Apache-2.0
"""Execution context — per-turn state for the execution brain."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from aethos_core.execution_brain.execution_goal import ExecutionGoal


@dataclass
class ExecutionContext:
    session_id: str
    goal: ExecutionGoal
    checks: dict[str, Any] = field(default_factory=dict)
    discovered_target: tuple[str, str, str] | None = None
    target_label: str = ""
    available_tools: list[str] = field(default_factory=list)
    mutation_execution_enabled: bool = False
    provider_env_mutations_enabled: bool = False
    prior_failures: list[str] = field(default_factory=list)
    active_job_id: str = ""
