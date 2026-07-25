# SPDX-License-Identifier: Apache-2.0
"""Canonical per-target operation lifecycle state."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from time import time
from typing import Any

from aethos_core.operations.mutations.lifecycle_authority import (
    AWAITING_APPROVAL,
    EXECUTION_COMPLETED_STATE,
    EXECUTION_FAILED_STATE,
    PROVIDER_MUTATION_REQUESTED_STATE,
    STABILIZING_STATE,
    VERIFICATION_RUNNING_STATE,
    VERIFIED_STATE,
    canonical_mutation_state,
)
from aethos_core.operations.preflight_supersede import preflight_match_key

_STORE: dict[str, OperationLifecycleState] = {}


@dataclass
class OperationLifecycleState:
    provider: str
    project: str | None
    environment: str | None
    service: str | None
    operation: str
    preflight_job_id: str | None = None
    execution_job_id: str | None = None
    approval_status: str = "not_required"
    execution_status: str = "none"
    verification_status: str = "none"
    canonical_state: str = "preflight_pending"
    started_at: float | None = None
    completed_at: float | None = None
    credential_blocked: bool = False
    latest_summary: str = ""
    session_id: str = "default"
    match_key: str = ""
    updated_at: float = field(default_factory=time)

    def target_path(self) -> str:
        parts = [p for p in (self.project, self.environment, self.service) if p]
        if parts:
            return " / ".join(parts)
        return self.service or "the target"

    def executed_recently(self, within_seconds: float) -> bool:
        ts = self.completed_at or self.updated_at
        return (time() - ts) <= within_seconds

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _store_key(session_id: str, match_key: str) -> str:
    return f"{session_id}:{match_key}"


def get_stored_operation_state(*, session_id: str, match_key: str) -> OperationLifecycleState | None:
    return _STORE.get(_store_key(session_id, match_key))


def list_session_operation_states(session_id: str) -> list[OperationLifecycleState]:
    prefix = f"{session_id}:"
    rows = [state for key, state in _STORE.items() if key.startswith(prefix)]
    rows.sort(key=lambda row: row.updated_at, reverse=True)
    return rows


def upsert_operation_state(state: OperationLifecycleState) -> OperationLifecycleState:
    key = _store_key(state.session_id, state.match_key)
    existing = _STORE.get(key)
    if existing and existing.updated_at > state.updated_at:
        return existing
    _STORE[key] = state
    try:
        from aethos_core.operation_lifecycle.global_lifecycle_index import index_mutation_lifecycle

        index_mutation_lifecycle(state)
    except Exception:
        pass
    return state


def _target_fields_from_job(params: dict[str, Any]) -> tuple[str | None, str | None, str | None]:
    target = dict(params.get("target") or {})
    pf = dict(params.get("mutation_preflight") or {})
    if not target and isinstance(pf.get("target"), dict):
        target = dict(pf["target"])
    project = target.get("project_name") or params.get("project_name")
    environment = target.get("environment") or params.get("environment") or "production"
    service = (
        params.get("target_name")
        or pf.get("target_name")
        or target.get("service_name")
    )
    return (
        str(project) if project else None,
        str(environment) if environment else None,
        str(service) if service else None,
    )


def _approval_status(params: dict[str, Any], canonical: str) -> str:
    if params.get("mutation_execution_approved"):
        return "approved"
    preflight = str(params.get("preflight_status") or "")
    if preflight in ("needs_credential", "needs_credential_repair", "needs_information"):
        return "blocked"
    if canonical == AWAITING_APPROVAL or preflight == "ready_for_mutation_approval":
        return "pending"
    return "not_required"


def _execution_status(params: dict[str, Any], canonical: str) -> str:
    if params.get("executed") is False or canonical == EXECUTION_FAILED_STATE:
        return "failed"
    if canonical == VERIFIED_STATE or params.get("verified") is True:
        return "completed"
    if canonical in {STABILIZING_STATE, VERIFICATION_RUNNING_STATE, PROVIDER_MUTATION_REQUESTED_STATE}:
        return "running"
    exec_state = str(params.get("execution_state") or "")
    if exec_state in {"provider_mutation_requested", "stabilizing"}:
        return "running"
    ver = str(params.get("verification_state") or "")
    if ver in {"verification_running", "verification_pending"}:
        return "running"
    if params.get("executed") is True or canonical in {
        EXECUTION_COMPLETED_STATE,
        STABILIZING_STATE,
        VERIFICATION_RUNNING_STATE,
    }:
        if ver == "verified" or params.get("verified") is True:
            return "completed"
        if canonical in {STABILIZING_STATE, VERIFICATION_RUNNING_STATE} or exec_state == "stabilizing":
            return "running"
        return "completed"
    if params.get("mutation_execution_job_id") or params.get("mutation_execution_approved"):
        return "running"
    return "none"


def _verification_status(params: dict[str, Any], canonical: str) -> str:
    ver = str(params.get("verification_state") or "")
    if ver == "verified" or params.get("verified") is True or canonical == VERIFIED_STATE:
        return "verified"
    if ver == "verification_failed":
        return "failed"
    if canonical == STABILIZING_STATE or str(params.get("execution_state") or "") == "stabilizing":
        return "stabilizing"
    if ver in {"verification_running", "verification_pending"} or params.get("verification_job_id"):
        return "running"
    if canonical in {EXECUTION_COMPLETED_STATE, VERIFICATION_RUNNING_STATE}:
        return "pending"
    return "none"


def _credential_blocked(params: dict[str, Any]) -> bool:
    preflight = str(params.get("preflight_status") or "")
    if preflight in ("needs_credential", "needs_credential_repair"):
        return True
    pf = dict(params.get("mutation_preflight") or {})
    pf_status = str(pf.get("preflight_status") or "")
    return pf_status in ("needs_credential", "needs_credential_repair")


def build_operation_state_from_job(job: Any) -> OperationLifecycleState | None:
    params = dict(getattr(job, "params", None) or {})
    pf = dict(params.get("mutation_preflight") or {})
    provider = str(params.get("provider") or pf.get("provider") or "")
    operation = str(params.get("operation_type") or pf.get("operation_type") or "")
    if not provider or not operation:
        return None

    project, environment, service = _target_fields_from_job(params)
    match_key = str(
        params.get("preflight_match_key")
        or preflight_match_key(provider=provider, operation_type=operation, target_name=service)
    )
    canonical = str(params.get("canonical_lifecycle_state") or canonical_mutation_state(params))
    summary = str(params.get("lifecycle_summary") or job.result_summary or "")

    preflight_id = None
    execution_id = None
    if getattr(job, "job_type", "") == "mutation_preflight":
        preflight_id = str(getattr(job, "id", "") or "")
        exec_raw = params.get("mutation_execution_job_id") or pf.get("mutation_execution_job_id")
        execution_id = str(exec_raw) if exec_raw else None
    elif getattr(job, "job_type", "") == "mutation_execution":
        execution_id = str(getattr(job, "id", "") or "")
        preflight_id = str(
            params.get("preflight_job_id")
            or params.get("source_mutation_preflight_job_id")
            or ""
        ) or None

    started = float(getattr(job, "created_at", 0) or 0) or None
    completed = None
    if _execution_status(params, canonical) == "completed":
        completed = float(getattr(job, "updated_at", 0) or started or 0) or None

    return OperationLifecycleState(
        provider=provider,
        project=project,
        environment=environment,
        service=service,
        operation=operation,
        preflight_job_id=preflight_id,
        execution_job_id=execution_id,
        approval_status=_approval_status(params, canonical),
        execution_status=_execution_status(params, canonical),
        verification_status=_verification_status(params, canonical),
        canonical_state=canonical,
        started_at=started,
        completed_at=completed,
        credential_blocked=_credential_blocked(params),
        latest_summary=summary,
        session_id=str(getattr(job, "session_id", "") or "default"),
        match_key=match_key,
        updated_at=float(getattr(job, "updated_at", 0) or time()),
    )


def upsert_operation_state_from_job(job: Any) -> OperationLifecycleState | None:
    state = build_operation_state_from_job(job)
    if state is None:
        return None
    return upsert_operation_state(state)


def refresh_operation_state_for_session(session_id: str) -> list[OperationLifecycleState]:
    from aethos_core.runtime.job_types import uses_mutation_execution, uses_mutation_preflight
    from aethos_core.runtime.jobs import job_store

    refreshed: list[OperationLifecycleState] = []
    for job in job_store.list_all():
        if str(getattr(job, "session_id", "") or "") != session_id:
            continue
        if not uses_mutation_preflight(job.job_type) and not uses_mutation_execution(job.job_type):
            continue
        state = upsert_operation_state_from_job(job)
        if state:
            refreshed.append(state)
    return refreshed


def reset_operation_state_store_for_tests() -> None:
    _STORE.clear()
