# SPDX-License-Identifier: Apache-2.0
"""Pending operational actions offered to the user."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

_MEMORY: dict[str, "PendingAction"] = {}
DEFAULT_TTL_HOURS = 2


@dataclass
class PendingAction:
    session_id: str
    type: str = "provider_retry_action"
    provider: str = "railway"
    project: str = ""
    environment: str = "production"
    service: str = ""
    operation: str = "restart"
    source_binding: str | None = None
    next_action: str = "create_mutation_preflight"
    status: str = "awaiting_user_confirmation"
    params: dict[str, Any] = field(default_factory=dict)
    expires_at: str = ""
    created_at: str = ""

    def service_path(self) -> str:
        return f"{self.project} / {self.environment} / {self.service}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "type": self.type,
            "provider": self.provider,
            "project": self.project,
            "environment": self.environment,
            "service": self.service,
            "operation": self.operation,
            "source_binding": self.source_binding,
            "next_action": self.next_action,
            "status": self.status,
            "params": dict(self.params),
            "expires_at": self.expires_at,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> PendingAction:
        return cls(
            session_id=str(raw.get("session_id") or ""),
            type=str(raw.get("type") or "provider_retry_action"),
            provider=str(raw.get("provider") or "railway"),
            project=str(raw.get("project") or ""),
            environment=str(raw.get("environment") or "production"),
            service=str(raw.get("service") or ""),
            operation=str(raw.get("operation") or "restart"),
            source_binding=raw.get("source_binding"),
            next_action=str(raw.get("next_action") or "create_mutation_preflight"),
            status=str(raw.get("status") or "awaiting_user_confirmation"),
            params=dict(raw.get("params") or {}),
            expires_at=str(raw.get("expires_at") or ""),
            created_at=str(raw.get("created_at") or ""),
        )


def _store_dir() -> Path:
    root = Path(__file__).resolve().parents[2] / "data" / "pending_actions"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _session_path(session_id: str) -> Path:
    safe = (session_id or "default").strip().replace("/", "_")[:128]
    return _store_dir() / f"{safe}.json"


def _expires_at(hours: int = DEFAULT_TTL_HOURS) -> str:
    return (datetime.now(UTC) + timedelta(hours=hours)).isoformat()


def _is_expired(action: PendingAction) -> bool:
    if not action.expires_at:
        return False
    try:
        deadline = datetime.fromisoformat(action.expires_at.replace("Z", "+00:00"))
    except ValueError:
        return True
    if deadline.tzinfo is None:
        deadline = deadline.replace(tzinfo=UTC)
    return datetime.now(UTC) >= deadline


def store_pending_action(action: PendingAction) -> PendingAction:
    action.created_at = action.created_at or datetime.now(UTC).isoformat()
    action.expires_at = action.expires_at or _expires_at()
    _MEMORY[action.session_id] = action
    path = _session_path(action.session_id)
    path.write_text(json.dumps(action.to_dict(), indent=2), encoding="utf-8")
    return action


def get_pending_action(*, session_id: str) -> PendingAction | None:
    session_id = (session_id or "default").strip()
    cached = _MEMORY.get(session_id)
    if cached is None:
        path = _session_path(session_id)
        if path.is_file():
            try:
                raw = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(raw, dict):
                    cached = PendingAction.from_dict(raw)
                    _MEMORY[session_id] = cached
            except (OSError, json.JSONDecodeError):
                return None
    if cached is None:
        return None
    if _is_expired(cached):
        clear_pending_action(session_id=session_id)
        return None
    # §1 — tighter conversational TTL: an abandoned pending action expires after a
    # few minutes so a stale confirmation prompt can't answer a later, fresh turn.
    from aethos_core.task_frame.continuation_ttl import is_frame_conversationally_stale

    if is_frame_conversationally_stale(cached.created_at):
        clear_pending_action(session_id=session_id)
        return None
    if cached.status in {"completed", "cancelled"}:
        return None
    return cached


def clear_pending_action(*, session_id: str) -> None:
    session_id = (session_id or "default").strip()
    _MEMORY.pop(session_id, None)
    path = _session_path(session_id)
    if path.is_file():
        path.unlink()


def offer_retry_preflight_action(
    *,
    session_id: str,
    provider: str,
    project: str,
    environment: str,
    service: str,
    operation: str = "restart",
    source_binding: str | None = None,
    params: dict[str, Any] | None = None,
) -> PendingAction:
    action = PendingAction(
        session_id=session_id,
        provider=provider,
        project=project,
        environment=environment,
        service=service,
        operation=operation,
        source_binding=source_binding,
        next_action="create_mutation_preflight",
        status="awaiting_user_confirmation",
        params=dict(params or {}),
    )
    return store_pending_action(action)


def clear_pending_actions_for_tests() -> None:
    _MEMORY.clear()
    root = _store_dir()
    for path in root.glob("*.json"):
        path.unlink()
