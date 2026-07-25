# SPDX-License-Identifier: Apache-2.0
"""Active operational thread state — mutation context per session."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class OperationalThreadState:
    session_id: str
    active_thread: str = "railway_mutation"
    provider: str = "railway"
    project: str | None = None
    environment: str | None = "production"
    service: str | None = None
    operation: str | None = None
    preflight_job_id: str | None = None
    execution_job_id: str | None = None
    status: str = "unknown"
    last_user_intent: str | None = None
    last_system_result: str | None = None
    next_check: str | None = None
    failure_reason: dict[str, Any] | None = None
    approved_at: str | None = None
    last_evidence: dict[str, Any] | None = None
    last_logs: list[dict[str, Any]] | None = None
    last_verified_at: str | None = None
    updated_at: str = ""
    expires_at: str | None = None

    def service_path(self) -> str:
        if self.project and self.service:
            env = self.environment or "production"
            return f"{self.project} / {env} / {self.service}"
        return str(self.service or "unknown")

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "active_thread": self.active_thread,
            "provider": self.provider,
            "project": self.project,
            "environment": self.environment,
            "service": self.service,
            "operation": self.operation,
            "preflight_job_id": self.preflight_job_id,
            "execution_job_id": self.execution_job_id,
            "status": self.status,
            "last_user_intent": self.last_user_intent,
            "last_system_result": self.last_system_result,
            "next_check": self.next_check,
            "failure_reason": dict(self.failure_reason) if isinstance(self.failure_reason, dict) else None,
            "approved_at": self.approved_at,
            "last_evidence": dict(self.last_evidence) if isinstance(self.last_evidence, dict) else None,
            "last_logs": list(self.last_logs) if isinstance(self.last_logs, list) else None,
            "last_verified_at": self.last_verified_at,
            "updated_at": self.updated_at,
            "expires_at": self.expires_at,
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> OperationalThreadState:
        return cls(
            session_id=str(raw.get("session_id") or ""),
            active_thread=str(raw.get("active_thread") or "railway_mutation"),
            provider=str(raw.get("provider") or "railway"),
            project=raw.get("project"),
            environment=raw.get("environment"),
            service=raw.get("service"),
            operation=raw.get("operation"),
            preflight_job_id=raw.get("preflight_job_id"),
            execution_job_id=raw.get("execution_job_id"),
            status=str(raw.get("status") or "unknown"),
            last_user_intent=raw.get("last_user_intent"),
            last_system_result=raw.get("last_system_result"),
            next_check=raw.get("next_check"),
            failure_reason=dict(raw.get("failure_reason") or {}) if raw.get("failure_reason") else None,
            approved_at=raw.get("approved_at"),
            last_evidence=dict(raw.get("last_evidence") or {}) if raw.get("last_evidence") else None,
            last_logs=list(raw.get("last_logs") or []) if raw.get("last_logs") else None,
            last_verified_at=raw.get("last_verified_at"),
            updated_at=str(raw.get("updated_at") or ""),
            expires_at=raw.get("expires_at"),
        )
