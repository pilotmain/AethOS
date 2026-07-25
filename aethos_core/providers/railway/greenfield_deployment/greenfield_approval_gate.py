# SPDX-License-Identifier: Apache-2.0
"""Approval gate validation for Railway greenfield preflight jobs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from aethos_core.config import get_settings
from aethos_core.jobs.session_approval_target import get_session_approval_target
from aethos_core.providers.railway.greenfield_deployment.greenfield_preflight import (
    RAILWAY_GREENFIELD_PREFLIGHT_JOB_TYPE,
)
from aethos_core.providers.vercel.greenfield_deployment.greenfield_preflight import (
    VERCEL_GREENFIELD_PREFLIGHT_JOB_TYPE,
)

_GREENFIELD_PREFLIGHT_JOB_TYPES = frozenset(
    {RAILWAY_GREENFIELD_PREFLIGHT_JOB_TYPE, VERCEL_GREENFIELD_PREFLIGHT_JOB_TYPE}
)

FailureState = Literal[
    "invalid_job",
    "not_greenfield_preflight",
    "session_mismatch",
    "approval_not_required",
    "already_approved",
    "already_mutated",
    "expired",
    "mutation_execution_disabled",
    "context_mismatch",
]


@dataclass
class GreenfieldApprovalGateResult:
    ok: bool
    failure_state: FailureState | None = None
    detail: str = ""
    required_action: str = ""
    safe_next_command: str = ""
    report: dict[str, Any] | None = None


class GreenfieldApprovalError(ValueError):
    def __init__(self, result: GreenfieldApprovalGateResult) -> None:
        self.result = result
        super().__init__(result.detail or result.failure_state or "approval blocked")


def _is_expired_target(*, session_id: str | None, job_id: str) -> bool:
    if not session_id:
        return False
    target = get_session_approval_target(session_id, job_id)
    if not target:
        return False
    from aethos_core.jobs.session_approval_target import list_active_session_approval_targets

    return job_id not in {row.latest_pending_job_id for row in list_active_session_approval_targets(session_id=session_id)}


def validate_greenfield_approval_gate(
    job: Any,
    *,
    session_id: str | None = None,
    remembered: dict[str, Any] | None = None,
) -> GreenfieldApprovalGateResult:
    if not job:
        return GreenfieldApprovalGateResult(
            ok=False,
            failure_state="invalid_job",
            detail="Job not found.",
            required_action="Create a new Railway greenfield preflight before approving.",
            safe_next_command="Ask AethOS to deploy the local workspace to Railway.",
        )

    if str(getattr(job, "job_type", "") or "") not in _GREENFIELD_PREFLIGHT_JOB_TYPES:
        return GreenfieldApprovalGateResult(
            ok=False,
            failure_state="not_greenfield_preflight",
            detail="Not a provider greenfield preflight job.",
        )

    job_session = str(getattr(job, "session_id", "") or "")
    if session_id and job_session and job_session != session_id:
        return GreenfieldApprovalGateResult(
            ok=False,
            failure_state="session_mismatch",
            detail="Job does not belong to the current session.",
            required_action="Approve the job from the session that created the preflight.",
        )

    params = dict(getattr(job, "params", None) or {})
    if not params.get("approval_required"):
        return GreenfieldApprovalGateResult(
            ok=False,
            failure_state="approval_not_required",
            detail="This greenfield preflight does not require approval.",
        )

    if params.get("greenfield_preflight_approved"):
        return GreenfieldApprovalGateResult(
            ok=False,
            failure_state="already_approved",
            detail="Greenfield preflight already approved.",
            required_action="Check Mission Control for orchestration progress.",
        )

    if params.get("mutation_performed"):
        return GreenfieldApprovalGateResult(
            ok=False,
            failure_state="already_mutated",
            detail="Railway mutations were already performed for this preflight.",
        )

    if session_id and _is_expired_target(session_id=session_id, job_id=str(getattr(job, "id", "") or "")):
        return GreenfieldApprovalGateResult(
            ok=False,
            failure_state="expired",
            detail="Approval target expired for this session.",
            required_action="Re-run the Railway greenfield preflight to obtain a fresh approval target.",
            safe_next_command="Repeat the local workspace Railway deployment request.",
        )

    remembered = remembered or {}
    if remembered:
        if remembered.get("provider") and remembered.get("provider") != params.get("provider"):
            return GreenfieldApprovalGateResult(
                ok=False,
                failure_state="context_mismatch",
                detail="Remembered provider does not match the pending job.",
            )
        if remembered.get("preflight_id") and remembered.get("preflight_id") != params.get("preflight_id"):
            return GreenfieldApprovalGateResult(
                ok=False,
                failure_state="context_mismatch",
                detail="Remembered preflight id does not match the pending job.",
            )

    settings = get_settings()
    checks = {
        "provider": params.get("provider"),
        "mutation_execution_enabled": settings.mutation_execution_enabled,
        "provider_env_var_mutations_enabled": settings.provider_env_var_mutations_enabled,
        "preflight_id": params.get("preflight_id"),
    }
    if not settings.mutation_execution_enabled:
        return GreenfieldApprovalGateResult(
            ok=False,
            failure_state="mutation_execution_disabled",
            detail="Set MUTATION_EXECUTION_ENABLED=true for governed execution.",
            required_action="Enable mutation execution, then reply approve again.",
            safe_next_command="approve",
            report=checks,
        )

    return GreenfieldApprovalGateResult(ok=True, report=checks)
