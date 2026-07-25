# SPDX-License-Identifier: Apache-2.0
"""Session-scoped pending approval targets — resolve short approval replies safely."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

DEFAULT_APPROVAL_TARGET_TTL_HOURS = 24

_PROVIDER_E2E_APPROVAL_ROUTE = "/api/v1/jobs/{job_id}/approve-provider-e2e-orchestration"
_GREENFIELD_APPROVAL_ROUTE = "/api/v1/jobs/{job_id}/approve-railway-greenfield-preflight"


@dataclass
class SessionApprovalTarget:
    session_id: str
    latest_pending_job_id: str
    job_type: str
    provider: str
    action_type: str
    preflight_id: str = ""
    approval_route: str = ""
    created_at: str = ""
    expires_at: str = ""
    mutation_performed: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "latest_pending_job_id": self.latest_pending_job_id,
            "job_type": self.job_type,
            "provider": self.provider,
            "action_type": self.action_type,
            "preflight_id": self.preflight_id,
            "approval_route": self.approval_route,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "mutation_performed": self.mutation_performed,
            "metadata": dict(self.metadata),
        }


_TARGETS: dict[str, list[SessionApprovalTarget]] = {}


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _expires_iso(hours: int = DEFAULT_APPROVAL_TARGET_TTL_HOURS) -> str:
    return (datetime.now(UTC) + timedelta(hours=hours)).isoformat()


def _is_expired(target: SessionApprovalTarget) -> bool:
    try:
        deadline = datetime.fromisoformat(str(target.expires_at).replace("Z", "+00:00"))
    except ValueError:
        return True
    if deadline.tzinfo is None:
        deadline = deadline.replace(tzinfo=UTC)
    return datetime.now(UTC) >= deadline


def approval_route_for_job(*, job_id: str, job_type: str) -> str:
    from aethos_core.provider_e2e_execution.job_taxonomy import PROVIDER_E2E_ORCHESTRATION_JOB_TYPE
    from aethos_core.providers.railway.greenfield_deployment.greenfield_preflight import (
        RAILWAY_GREENFIELD_PREFLIGHT_JOB_TYPE,
    )
    from aethos_core.provider_e2e_orchestration.env_completion.supabase_constants import (
        SUPABASE_ENV_COMPLETION_JOB_TYPE,
    )
    from aethos_core.providers.vercel.greenfield_deployment.greenfield_preflight import (
        VERCEL_GREENFIELD_PREFLIGHT_JOB_TYPE,
    )

    if job_type == PROVIDER_E2E_ORCHESTRATION_JOB_TYPE:
        return _PROVIDER_E2E_APPROVAL_ROUTE.format(job_id=job_id)
    if job_type == RAILWAY_GREENFIELD_PREFLIGHT_JOB_TYPE:
        return _GREENFIELD_APPROVAL_ROUTE.format(job_id=job_id)
    if job_type == VERCEL_GREENFIELD_PREFLIGHT_JOB_TYPE:
        return f"/api/v1/jobs/{job_id}/approve-vercel-greenfield-preflight"
    if job_type == SUPABASE_ENV_COMPLETION_JOB_TYPE:
        return f"/api/v1/jobs/{job_id}/approve-supabase-env-completion"
    return _PROVIDER_E2E_APPROVAL_ROUTE.format(job_id=job_id)


def record_session_approval_target(
    *,
    session_id: str,
    job_id: str,
    job_type: str,
    provider: str,
    action_type: str,
    preflight_id: str = "",
    approval_route: str | None = None,
    expires_at: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> SessionApprovalTarget:
    """Remember the latest pending approval target for a chat session."""
    route = approval_route or approval_route_for_job(job_id=job_id, job_type=job_type)
    target = SessionApprovalTarget(
        session_id=session_id,
        latest_pending_job_id=job_id,
        job_type=job_type,
        provider=provider,
        action_type=action_type,
        preflight_id=preflight_id,
        approval_route=route,
        created_at=_now_iso(),
        expires_at=expires_at or _expires_iso(),
        mutation_performed=False,
        metadata=dict(metadata or {}),
    )
    rows = _TARGETS.setdefault(session_id, [])
    rows[:] = [row for row in rows if row.latest_pending_job_id != job_id]
    rows.append(target)
    return target


def mark_session_approval_mutation_performed(*, session_id: str, job_id: str) -> None:
    for target in _TARGETS.get(session_id, []):
        if target.latest_pending_job_id == job_id:
            target.mutation_performed = True


def get_session_approval_target(session_id: str, job_id: str) -> SessionApprovalTarget | None:
    for target in _TARGETS.get(session_id, []):
        if target.latest_pending_job_id == job_id:
            return target
    return None


def list_active_session_approval_targets(*, session_id: str) -> list[SessionApprovalTarget]:
    active: list[SessionApprovalTarget] = []
    for target in _TARGETS.get(session_id, []):
        if target.mutation_performed:
            continue
        if _is_expired(target):
            continue
        active.append(target)
    return active


def list_expired_unapproved_targets(*, session_id: str) -> list[SessionApprovalTarget]:
    expired: list[SessionApprovalTarget] = []
    for target in _TARGETS.get(session_id, []):
        if target.mutation_performed:
            continue
        if not _is_expired(target):
            continue
        expired.append(target)
    return expired


def clear_session_approval_targets_for_tests() -> None:
    _TARGETS.clear()
