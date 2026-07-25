# SPDX-License-Identifier: Apache-2.0
"""Load post-mutation verification context from lifecycle and execution jobs."""

from __future__ import annotations

from dataclasses import dataclass, field
from time import time
from typing import Any

from aethos_core.operation_lifecycle.operation_state_store import OperationLifecycleState


def resolve_verification_lifecycle_state(
    *,
    session_id: str = "default",
    text: str | None = None,
    lifecycle: OperationLifecycleState | None = None,
) -> OperationLifecycleState | None:
    """Resolve lifecycle state using explicit service names only."""
    if lifecycle is not None:
        return lifecycle
    from aethos_core.post_mutation_verification.verification_context_discovery import (
        discover_verification_lifecycle,
    )

    discovered = discover_verification_lifecycle(text or "", session_id=session_id)
    if discovered is not None:
        return discovered

    from aethos_core.post_mutation_verification.verification_intent_router import (
        is_intent_word,
        resolve_verification_target,
    )

    target = resolve_verification_target(text or "", session_id=session_id)
    if target is None:
        return None

    from aethos_core.operation_lifecycle.lifecycle_resolver import find_latest_mutation_lifecycle_across_sessions

    service = target.service
    if service and is_intent_word(service):
        service = None
    return find_latest_mutation_lifecycle_across_sessions(
        session_id=session_id,
        provider=target.provider,
        service=service,
    )


@dataclass
class VerificationContext:
    session_id: str
    lifecycle: OperationLifecycleState
    execution_job_id: str | None = None
    execution_params: dict[str, Any] = field(default_factory=dict)
    provider: str = ""
    operation: str = ""
    target_path: str = ""
    service: str | None = None
    execution_completed: bool = False
    provider_command_submitted: bool = False
    verification_state: str = ""
    restart_verification_state: str = ""
    before_snapshot: dict[str, Any] | None = None
    after_snapshot: dict[str, Any] | None = None
    verification_artifact: dict[str, Any] | None = None
    provider_result: dict[str, Any] = field(default_factory=dict)
    lifecycle_summary: str = ""
    log_summary: str = ""
    service_health: str = "unknown"
    deployment_status_before: str = ""
    deployment_status_after: str = ""
    last_checked_at: float | None = None

    def to_dict(self) -> dict[str, str]:
        return {
            "execution_job_id": self.execution_job_id or "",
            "provider": self.provider,
            "operation": self.operation,
            "target_path": self.target_path,
            "verification_state": self.verification_state,
            "restart_verification_state": self.restart_verification_state,
            "service_health": self.service_health,
            "provider_command_submitted": str(self.provider_command_submitted).lower(),
            "post_mutation_verification_status": self.verification_state,
        }


def load_verification_context(
    *,
    session_id: str = "default",
    text: str | None = None,
    lifecycle: OperationLifecycleState | None = None,
) -> VerificationContext | None:
    state = lifecycle or resolve_verification_lifecycle_state(session_id=session_id, text=text)
    if state is None:
        return None
    if state.execution_status not in {"completed", "running"} and state.canonical_state not in {
        "execution_completed",
        "verification_running",
        "stabilizing",
        "verified",
    }:
        return None

    execution_params: dict[str, Any] = {}
    execution_job = None
    if state.execution_job_id:
        from aethos_core.runtime.jobs import job_store

        execution_job = job_store.get(state.execution_job_id)
        if execution_job:
            execution_params = dict(getattr(execution_job, "params", None) or {})
    if not execution_params and state.execution_job_id:
        from aethos_core.operation_lifecycle.global_lifecycle_index import get_execution_params_snapshot

        execution_params = get_execution_params_snapshot(state.execution_job_id)

    provider_result = execution_params.get("provider_result") or {}
    if not isinstance(provider_result, dict):
        provider_result = {}
    exec_artifact = execution_params.get("mutation_execution") or {}
    if isinstance(exec_artifact, dict):
        nested = exec_artifact.get("provider_result")
        if isinstance(nested, dict) and not provider_result:
            provider_result = nested

    before = execution_params.get("railway_before_snapshot")
    if not isinstance(before, dict):
        before = None
    after = execution_params.get("railway_after_snapshot")
    if not isinstance(after, dict):
        after = None

    verification_artifact = execution_params.get("verification_artifact")
    if not isinstance(verification_artifact, dict):
        verification_artifact = None

    log_summary = _log_summary_from_params(execution_params, verification_artifact)
    service_health = str(
        execution_params.get("restart_service_health")
        or provider_result.get("service_health")
        or _health_from_snapshots(before, after)
        or "unknown"
    )
    deployment_before = str(
        (before or {}).get("latest_deployment_status")
        or execution_params.get("deployment_state_before")
        or ""
    )
    deployment_after = str(
        (after or {}).get("latest_deployment_status")
        or execution_params.get("deployment_state_after")
        or provider_result.get("deployment_state_after")
        or ""
    )

    return VerificationContext(
        session_id=session_id,
        lifecycle=state,
        execution_job_id=state.execution_job_id,
        execution_params=execution_params,
        provider=state.provider,
        operation=state.operation,
        target_path=state.target_path(),
        service=state.service,
        execution_completed=state.execution_status == "completed" or execution_params.get("executed") is True,
        provider_command_submitted=bool(
            execution_params.get("restart_command_submitted")
            or provider_result.get("restart_command_submitted")
            or provider_result.get("ok")
        ),
        verification_state=str(execution_params.get("verification_state") or state.verification_status or ""),
        restart_verification_state=str(execution_params.get("restart_verification_state") or ""),
        before_snapshot=before,
        after_snapshot=after,
        verification_artifact=verification_artifact,
        provider_result=provider_result,
        lifecycle_summary=str(execution_params.get("lifecycle_summary") or state.latest_summary or ""),
        log_summary=log_summary,
        service_health=service_health,
        deployment_status_before=deployment_before,
        deployment_status_after=deployment_after,
        last_checked_at=float(execution_params.get("verification_completed_at") or execution_params.get("updated_at") or time()),
    )


def _health_from_snapshots(before: dict[str, Any] | None, after: dict[str, Any] | None) -> str:
    after_status = str((after or {}).get("latest_deployment_status") or "").lower()
    if after_status in {"success", "active", "running", "ready"}:
        return "healthy"
    if after_status in {"failed", "crashed", "error"}:
        return "failed"
    before_status = str((before or {}).get("latest_deployment_status") or "").lower()
    if before_status in {"failed", "crashed", "error"} and not after_status:
        return "unknown"
    return "unknown"


def _log_summary_from_params(
    params: dict[str, Any],
    verification_artifact: dict[str, Any] | None,
) -> str:
    bundle = params.get("provider_evidence_bundle")
    if isinstance(bundle, dict):
        logs = bundle.get("logs") or bundle.get("log_summary")
        if isinstance(logs, str) and logs.strip():
            return logs.strip()[:400]
    if verification_artifact:
        evidence = verification_artifact.get("evidence") or {}
        if isinstance(evidence, dict):
            readonly = evidence.get("readonly_execution") or {}
            if isinstance(readonly, dict):
                summary = str(readonly.get("summary") or "")
                if summary:
                    return summary[:400]
            restart_state = str(evidence.get("restart_verification_state") or "")
            if restart_state:
                return restart_state.replace("_", " ")
    restart_state = str(params.get("restart_verification_state") or "")
    if restart_state:
        return restart_state.replace("_", " ")
    return ""
