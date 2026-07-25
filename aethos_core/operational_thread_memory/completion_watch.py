# SPDX-License-Identifier: Apache-2.0
"""Completion watches for active operational threads."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

_MEMORY: dict[str, "CompletionWatch"] = {}
DEFAULT_TTL_HOURS = 8


@dataclass
class CompletionWatch:
    session_id: str
    provider: str = "railway"
    project: str = ""
    environment: str = "production"
    service: str = ""
    operation: str = "restart"
    execution_job_id: str = ""
    status: str = "watching"
    created_at: str = ""
    expires_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "provider": self.provider,
            "project": self.project,
            "environment": self.environment,
            "service": self.service,
            "operation": self.operation,
            "execution_job_id": self.execution_job_id,
            "status": self.status,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> CompletionWatch:
        return cls(
            session_id=str(raw.get("session_id") or ""),
            provider=str(raw.get("provider") or "railway"),
            project=str(raw.get("project") or ""),
            environment=str(raw.get("environment") or "production"),
            service=str(raw.get("service") or ""),
            operation=str(raw.get("operation") or "restart"),
            execution_job_id=str(raw.get("execution_job_id") or ""),
            status=str(raw.get("status") or "watching"),
            created_at=str(raw.get("created_at") or ""),
            expires_at=str(raw.get("expires_at") or ""),
        )


def _store_dir() -> Path:
    root = Path(__file__).resolve().parents[2] / "data" / "completion_watches"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _session_path(session_id: str) -> Path:
    safe = (session_id or "default").strip().replace("/", "_")[:128]
    return _store_dir() / f"{safe}.json"


def _expires_at(hours: int = DEFAULT_TTL_HOURS) -> str:
    return (datetime.now(UTC) + timedelta(hours=hours)).isoformat()


def create_completion_watch(
    *,
    session_id: str,
    provider: str,
    project: str,
    environment: str,
    service: str,
    operation: str,
    execution_job_id: str,
) -> CompletionWatch:
    watch = CompletionWatch(
        session_id=session_id,
        provider=provider,
        project=project,
        environment=environment,
        service=service,
        operation=operation,
        execution_job_id=execution_job_id,
        status="watching",
        created_at=datetime.now(UTC).isoformat(),
        expires_at=_expires_at(),
    )
    _MEMORY[session_id] = watch
    _session_path(session_id).write_text(json.dumps(watch.to_dict(), indent=2), encoding="utf-8")
    return watch


def get_completion_watch(*, session_id: str) -> CompletionWatch | None:
    session_id = (session_id or "default").strip()
    cached = _MEMORY.get(session_id)
    if cached is None:
        path = _session_path(session_id)
        if path.is_file():
            try:
                raw = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(raw, dict):
                    cached = CompletionWatch.from_dict(raw)
                    _MEMORY[session_id] = cached
            except (OSError, json.JSONDecodeError):
                return None
    if cached is None:
        return None
    if cached.expires_at:
        try:
            deadline = datetime.fromisoformat(cached.expires_at.replace("Z", "+00:00"))
            if deadline.tzinfo is None:
                deadline = deadline.replace(tzinfo=UTC)
            if datetime.now(UTC) >= deadline:
                clear_completion_watch(session_id=session_id)
                return None
        except ValueError:
            pass
    return cached


def clear_completion_watch(*, session_id: str) -> None:
    session_id = (session_id or "default").strip()
    _MEMORY.pop(session_id, None)
    path = _session_path(session_id)
    if path.is_file():
        path.unlink()


def clear_completion_watches_for_tests() -> None:
    _MEMORY.clear()
    root = _store_dir()
    for path in root.glob("*.json"):
        path.unlink()
