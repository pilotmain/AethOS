# SPDX-License-Identifier: Apache-2.0
"""Safe source binding update proposal and confirmation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from aethos_core.provider_topology.source_binding import SourceBinding
from aethos_core.provider_topology.topology_memory import get_binding, save_binding
from aethos_core.provider_topology.topology_refresh import refresh_service_topology

_PENDING: dict[str, "PendingBindingCorrection"] = {}
DEFAULT_TTL_HOURS = 2


@dataclass
class PendingBindingCorrection:
    session_id: str
    provider: str
    project: str
    environment: str
    service_name: str
    old_repo: str | None
    new_repo: str
    access_verified: bool = False
    auto_update_allowed: bool = False
    expires_at: str = ""

    def service_path(self) -> str:
        return f"{self.project} / {self.environment} / {self.service_name}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "provider": self.provider,
            "project": self.project,
            "environment": self.environment,
            "service_name": self.service_name,
            "old_repo": self.old_repo,
            "new_repo": self.new_repo,
            "access_verified": self.access_verified,
            "auto_update_allowed": self.auto_update_allowed,
            "expires_at": self.expires_at,
        }


def _expires_at(hours: int = DEFAULT_TTL_HOURS) -> str:
    return (datetime.now(UTC) + timedelta(hours=hours)).isoformat()


def _is_expired(pending: PendingBindingCorrection) -> bool:
    try:
        deadline = datetime.fromisoformat(pending.expires_at.replace("Z", "+00:00"))
    except ValueError:
        return True
    if deadline.tzinfo is None:
        deadline = deadline.replace(tzinfo=UTC)
    return datetime.now(UTC) >= deadline


def store_pending_correction(pending: PendingBindingCorrection) -> PendingBindingCorrection:
    pending.expires_at = pending.expires_at or _expires_at()
    _PENDING[pending.session_id] = pending
    return pending


def get_pending_correction(*, session_id: str) -> PendingBindingCorrection | None:
    pending = _PENDING.get(session_id)
    if pending is None:
        return None
    if _is_expired(pending):
        _PENDING.pop(session_id, None)
        return None
    return pending


def clear_pending_correction(*, session_id: str) -> None:
    _PENDING.pop(session_id, None)


def clear_pending_corrections_for_tests() -> None:
    _PENDING.clear()


def apply_binding_update(
    *,
    provider: str,
    project: str,
    environment: str,
    service_name: str,
    github_repo: str,
    service_id: str | None = None,
) -> dict[str, Any]:
    existing = get_binding(provider=provider, project=project, environment=environment, service_name=service_name)
    binding = SourceBinding(
        provider=provider,
        project=project,
        environment=environment,
        service_name=service_name,
        service_id=service_id or (existing.service_id if existing else None),
        github_repo=github_repo,
        github_installation_id=existing.github_installation_id if existing else None,
        domains=list(existing.domains or []) if existing else [],
        source_verified=True,
        updated_at=datetime.now(UTC).isoformat(),
    )
    save_binding(binding)
    graph = refresh_service_topology(
        provider=provider,
        project=project,
        environment=environment,
        service_name=service_name,
        github_repo=github_repo,
        force=True,
    )
    binding = get_binding(provider=provider, project=project, environment=environment, service_name=service_name)
    if binding is not None:
        binding.source_verified = True
        binding.github_repo = github_repo
        save_binding(binding)
    return {"ok": True, "binding": binding.to_dict() if binding else {}, "topology": graph.to_dict() if graph else None}


def confirm_pending_update(*, session_id: str) -> dict[str, Any]:
    pending = get_pending_correction(session_id=session_id)
    if pending is None:
        return {"ok": False, "error": "No pending binding correction for this session."}
    if not pending.access_verified:
        return {"ok": False, "error": "GitHub access was not verified for the pending repository."}
    outcome = apply_binding_update(
        provider=pending.provider,
        project=pending.project,
        environment=pending.environment,
        service_name=pending.service_name,
        github_repo=pending.new_repo,
    )
    clear_pending_correction(session_id=session_id)
    outcome["service_path"] = pending.service_path()
    outcome["old_repo"] = pending.old_repo
    outcome["new_repo"] = pending.new_repo
    return outcome
