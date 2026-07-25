# SPDX-License-Identifier: Apache-2.0
"""Session-scoped approval grants — bounded, never broad autonomy."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

_READONLY_SCOPE_RX = re.compile(
    r"\ballow\s+readonly\s+(?:railway|rail\s*way)\s+(?:checks?|operations?)\s+(?:this\s+)?session\b",
    re.I,
)
_MUTATION_SCOPE_RX = re.compile(
    r"\bapprove\s+(?:railway|rail\s*way)\s+(restarts?|redeploys?|deploys?)\s+for\s+(.+?)\s+(?:this\s+)?session\b",
    re.I,
)
_ONCE_SCOPE_RX = re.compile(r"\bapprove\s+(?:this\s+)?(?:railway\s+)?(?:restart|redeploy|mutation)\s+once\b", re.I)


@dataclass
class SessionApprovalScope:
    session_id: str
    scope_type: str
    provider: str
    operation: str | None = None
    project: str | None = None
    environment: str | None = None
    service: str | None = None
    risk_tier: str | None = None
    readonly: bool = False
    expires_at: str = ""
    granted_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "scope_type": self.scope_type,
            "provider": self.provider,
            "operation": self.operation,
            "project": self.project,
            "environment": self.environment,
            "service": self.service,
            "risk_tier": self.risk_tier,
            "readonly": self.readonly,
            "expires_at": self.expires_at,
            "granted_at": self.granted_at,
        }


_SCOPES: dict[str, list[SessionApprovalScope]] = {}


def _expires(hours: int = 8) -> str:
    return (datetime.now(UTC) + timedelta(hours=hours)).isoformat()


def _is_expired(scope: SessionApprovalScope) -> bool:
    try:
        deadline = datetime.fromisoformat(scope.expires_at.replace("Z", "+00:00"))
    except ValueError:
        return True
    if deadline.tzinfo is None:
        deadline = deadline.replace(tzinfo=UTC)
    return datetime.now(UTC) >= deadline


def grant_readonly_railway_session(*, session_id: str) -> SessionApprovalScope:
    scope = SessionApprovalScope(
        session_id=session_id,
        scope_type="session_readonly",
        provider="railway",
        readonly=True,
        granted_at=datetime.now(UTC).isoformat(),
        expires_at=_expires(),
    )
    _SCOPES.setdefault(session_id, []).append(scope)
    return scope


def grant_mutation_session(
    *,
    session_id: str,
    operation: str,
    target_phrase: str,
) -> SessionApprovalScope:
    parts = [p.strip() for p in target_phrase.replace("—", "/").split("/")]
    project = parts[0] if len(parts) >= 3 else None
    environment = parts[1] if len(parts) >= 3 else "production"
    service = parts[-1].strip() if parts else target_phrase.strip()
    scope = SessionApprovalScope(
        session_id=session_id,
        scope_type="session_mutation",
        provider="railway",
        operation=operation.rstrip("s"),
        project=project,
        environment=environment,
        service=service,
        granted_at=datetime.now(UTC).isoformat(),
        expires_at=_expires(hours=4),
    )
    _SCOPES.setdefault(session_id, []).append(scope)
    return scope


def has_readonly_railway_scope(*, session_id: str) -> bool:
    for scope in _SCOPES.get(session_id, []):
        if scope.readonly and scope.provider == "railway" and not _is_expired(scope):
            return True
    return False


def has_session_mutation_scope(
    *,
    session_id: str,
    provider: str,
    operation: str,
    project: str | None,
    environment: str | None,
    service: str | None,
) -> bool:
    for scope in _SCOPES.get(session_id, []):
        if _is_expired(scope) or scope.readonly:
            continue
        if scope.provider != provider or scope.operation != operation:
            continue
        if scope.service and service and scope.service.lower() != service.lower():
            continue
        if scope.project and project and scope.project.lower() != project.lower():
            continue
        if scope.environment and environment and scope.environment.lower() != environment.lower():
            continue
        return True
    return False


def compose_session_scope_reply(text: str, *, session_id: str = "default") -> tuple[str, str, dict[str, str]] | None:
    raw = (text or "").strip()
    if _READONLY_SCOPE_RX.search(raw):
        grant_readonly_railway_session(session_id=session_id)
        return (
            "Got it — **readonly Railway checks** (inventory, logs, status, diagnosis) are allowed for this session.\n\n"
            "**Mutations still require explicit approval.**",
            "session_approval_readonly",
            {"session_id": session_id, "provider": "railway"},
        )
    match = _MUTATION_SCOPE_RX.search(raw)
    if match:
        operation = match.group(1).lower().rstrip("s")
        target = match.group(2).strip()
        scope = grant_mutation_session(session_id=session_id, operation=operation, target_phrase=target)
        path = f"{scope.project} / {scope.environment} / {scope.service}" if scope.project else scope.service
        return (
            f"Scoped session approval granted for **Railway {operation}** on **{path}** only.\n\n"
            "This does not approve other services, operations, or providers. High-risk mutations may still require explicit approval.",
            "session_approval_mutation",
            {"session_id": session_id, "provider": "railway", "operation": operation, "service": str(scope.service or "")},
        )
    if _ONCE_SCOPE_RX.search(raw):
        return (
            "Understood — the **next approved mutation** in this session can proceed after you confirm in Mission Control.\n\n"
            "This is a one-time intent marker; execution still requires governed preflight approval.",
            "session_approval_once",
            {"session_id": session_id},
        )
    return None


def clear_session_scopes_for_tests() -> None:
    _SCOPES.clear()
