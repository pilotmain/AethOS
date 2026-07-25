# SPDX-License-Identifier: Apache-2.0
"""Operation preflight artifact — read-only planning before any mutation."""

from __future__ import annotations

from dataclasses import dataclass, field
from time import time
from typing import Any
from uuid import uuid4


def _new_operation_id() -> str:
    return f"opf-{uuid4().hex[:12]}"


@dataclass
class OperationPreflight:
    provider: str
    operation_type: str
    target_name: str | None
    target_status: str
    operation_id: str = field(default_factory=_new_operation_id)
    read_only: bool = True
    mutation_required: bool = True
    risk_level: str = "medium"
    required_approval: bool = True
    execution_enabled: bool = False
    read_only_execution_enabled: bool = False
    mutation_execution_enabled: bool = False
    approval_required: bool = True
    phase: str = "9.3B"
    execution_approved: bool = False
    execution_job_id: str | None = None
    current_state: dict[str, Any] = field(default_factory=dict)
    proposed_steps: list[str] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    missing_information: list[str] = field(default_factory=list)
    next_action: str = "approval_required_before_execution"
    preflight_status: str = "ready_for_approval"
    created_at: float = field(default_factory=time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "operation_id": self.operation_id,
            "provider": self.provider,
            "operation_type": self.operation_type,
            "target_name": self.target_name,
            "target_status": self.target_status,
            "read_only": self.read_only,
            "mutation_required": self.mutation_required,
            "risk_level": self.risk_level,
            "required_approval": self.required_approval,
            "execution_enabled": self.execution_enabled,
            "read_only_execution_enabled": self.read_only_execution_enabled,
            "mutation_execution_enabled": self.mutation_execution_enabled,
            "approval_required": self.approval_required,
            "phase": self.phase,
            "execution_approved": self.execution_approved,
            "execution_job_id": self.execution_job_id,
            "current_state": dict(self.current_state),
            "proposed_steps": list(self.proposed_steps),
            "blockers": list(self.blockers),
            "missing_information": list(self.missing_information),
            "next_action": self.next_action,
            "preflight_status": self.preflight_status,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> OperationPreflight:
        return cls(
            operation_id=str(data.get("operation_id") or _new_operation_id()),
            provider=str(data.get("provider") or "unknown"),
            operation_type=str(data.get("operation_type") or "unknown"),
            target_name=data.get("target_name"),
            target_status=str(data.get("target_status") or "unknown"),
            read_only=bool(data.get("read_only", True)),
            mutation_required=bool(data.get("mutation_required", True)),
            risk_level=str(data.get("risk_level") or "medium"),
            required_approval=bool(data.get("required_approval", True)),
            execution_enabled=bool(data.get("execution_enabled", False)),
            read_only_execution_enabled=bool(data.get("read_only_execution_enabled", False)),
            mutation_execution_enabled=bool(data.get("mutation_execution_enabled", False)),
            approval_required=bool(data.get("approval_required", data.get("required_approval", True))),
            phase=str(data.get("phase") or "9.3B"),
            execution_approved=bool(data.get("execution_approved", False)),
            execution_job_id=data.get("execution_job_id"),
            current_state=dict(data.get("current_state") or {}),
            proposed_steps=list(data.get("proposed_steps") or []),
            blockers=list(data.get("blockers") or []),
            missing_information=list(data.get("missing_information") or []),
            next_action=str(data.get("next_action") or "approval_required_before_execution"),
            preflight_status=str(data.get("preflight_status") or "ready_for_approval"),
            created_at=float(data.get("created_at") or time()),
        )
