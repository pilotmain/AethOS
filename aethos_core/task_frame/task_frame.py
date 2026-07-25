# SPDX-License-Identifier: Apache-2.0
"""Active task frame — operational task state per session."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class TaskCandidate:
    index: int
    project: str
    environment: str
    service: str
    service_id: str | None = None
    path: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "index": self.index,
            "project": self.project,
            "environment": self.environment,
            "service": self.service,
            "service_id": self.service_id,
            "path": self.path or f"{self.project} / {self.environment} / {self.service}",
            "raw": dict(self.raw),
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> TaskCandidate:
        return cls(
            index=int(raw.get("index") or 0),
            project=str(raw.get("project") or raw.get("project_name") or ""),
            environment=str(raw.get("environment") or "production"),
            service=str(raw.get("service") or raw.get("service_name") or ""),
            service_id=raw.get("service_id"),
            path=raw.get("path"),
            raw=dict(raw.get("raw") or raw),
        )


@dataclass
class TaskFrame:
    session_id: str
    task_id: str
    intent: str
    provider: str
    operation: str
    status: str
    candidates: list[TaskCandidate] = field(default_factory=list)
    next_action: str = "create_mutation_preflight_after_selection"
    original_request: str = ""
    params: dict[str, Any] = field(default_factory=dict)
    created_at: str = ""
    updated_at: str = ""
    expires_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "task_id": self.task_id,
            "intent": self.intent,
            "provider": self.provider,
            "operation": self.operation,
            "status": self.status,
            "candidates": [c.to_dict() for c in self.candidates],
            "next_action": self.next_action,
            "original_request": self.original_request,
            "params": dict(self.params),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "expires_at": self.expires_at,
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> TaskFrame:
        candidates = [TaskCandidate.from_dict(row) for row in (raw.get("candidates") or []) if isinstance(row, dict)]
        return cls(
            session_id=str(raw.get("session_id") or ""),
            task_id=str(raw.get("task_id") or ""),
            intent=str(raw.get("intent") or ""),
            provider=str(raw.get("provider") or ""),
            operation=str(raw.get("operation") or ""),
            status=str(raw.get("status") or ""),
            candidates=candidates,
            next_action=str(raw.get("next_action") or "create_mutation_preflight_after_selection"),
            original_request=str(raw.get("original_request") or ""),
            params=dict(raw.get("params") or {}),
            created_at=str(raw.get("created_at") or ""),
            updated_at=str(raw.get("updated_at") or ""),
            expires_at=raw.get("expires_at"),
        )
