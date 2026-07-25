# SPDX-License-Identifier: Apache-2.0
"""Shared types for governed real-mutation executors."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class RealMutationExecutionResult:
    journal: dict[str, Any]
    mutation_performed: bool = False
    idempotent_replay: bool = False
    service_id: str = ""
    executed_phases: list[str] = field(default_factory=list)
    detail: str = ""
    policy_blocked: bool = False
    errors: list[str] = field(default_factory=list)
