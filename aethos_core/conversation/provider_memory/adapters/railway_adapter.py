# SPDX-License-Identifier: Apache-2.0
"""Railway evidence adapter — first provider implementation."""

from __future__ import annotations

from typing import Any

from aethos_core.conversation.provider_memory.provider_evidence_adapter import (
    OperationStatus,
    OperationVerification,
    ProviderEvidenceAdapter,
    ProviderLogEntry,
)


class RailwayEvidenceAdapter(ProviderEvidenceAdapter):
    provider = "railway"

    def get_operation_status(self, thread: Any, job: Any | None) -> OperationStatus:
        verification = self.verify_operation(thread, job)
        status_label, verification_label = _status_labels(thread, job)
        command = verification.provider_command
        evidence = "detected" if verification.verified or verification.timestamp_after_approval else "not detected"
        if verification.conclusion in {"restart_verified", "restart_evidence_detected"}:
            evidence = "detected"
        return OperationStatus(
            execution_job_id=str(getattr(job, "id", "") or getattr(thread, "execution_job_id", "") or "unknown"),
            provider_command=command,
            restart_evidence=evidence,
            latest_log_timestamp=verification.latest_log_timestamp,
            service_health=verification.service_health,
            status_label=status_label,
            verification_label=verification_label,
        )

    def get_latest_logs(
        self,
        thread: Any,
        job: Any | None,
        *,
        limit: int = 5,
        level_filter: str | None = None,
    ) -> list[ProviderLogEntry]:
        evidence = _refresh_evidence(job)
        entries = list(evidence.entries or [])
        if level_filter:
            needle = level_filter.lower()
            entries = [entry for entry in entries if needle in (entry.level or "").lower()]
        selected = entries[-limit:] if limit else entries
        selected.reverse()
        return [
            ProviderLogEntry(timestamp=entry.timestamp, level=entry.level, message=entry.message)
            for entry in selected
        ]

    def verify_operation(self, thread: Any, job: Any | None) -> OperationVerification:
        evidence = _refresh_evidence(job)
        command = _provider_command_state(job)
        verified = evidence.conclusion in {"restart_verified", "restart_evidence_detected"}
        return OperationVerification(
            conclusion=evidence.conclusion,
            verified=verified,
            approval_time=evidence.approval_time,
            latest_log_timestamp=evidence.latest_timestamp,
            startup_after_approval=evidence.startup_after_approval,
            timestamp_after_approval=evidence.timestamp_after_approval,
            timestamps_available=evidence.timestamps_available,
            logs_unavailable=evidence.logs_unavailable,
            service_health=str(evidence.service_health or "unknown"),
            provider_command=command,
            evidence=evidence.to_dict(),
        )

    def explain_failure(self, thread: Any, job: Any | None) -> str:
        if job is not None:
            from aethos_core.provider_topology.failure_truth_expander import compose_expanded_failure_reply, expand_failure_truth

            truth = (getattr(job, "params", None) or {}).get("failure_truth") or expand_failure_truth(job)
            if truth:
                return compose_expanded_failure_reply(truth)

        failure = getattr(thread, "failure_reason", None) or {}
        path = thread.service_path()
        if failure.get("failure_reason"):
            return (
                f"The latest Railway **{getattr(thread, 'operation', 'mutation') or 'mutation'}** for **{path}** did not succeed.\n\n"
                f"Reason:\n{failure.get('failure_reason')}\n\n"
                f"Stage: `{failure.get('failure_stage')}`\n\n"
                f"Next recommended action:\n{failure.get('next_recommended_action') or getattr(thread, 'next_check', 'Review execution evidence.')}"
            )
        return (
            f"I checked the active Railway thread for **{path}**, but no structured failure reason is stored yet.\n\n"
            f"Current status: **{getattr(thread, 'status', 'unknown')}**."
        )


def _refresh_evidence(job: Any | None, *, bypass_cache: bool = True):
    from aethos_core.operational_thread_memory.railway_log_evidence import refresh_restart_log_evidence

    if job is None:
        from aethos_core.operational_thread_memory.railway_log_evidence import RestartLogEvidence

        return RestartLogEvidence(logs_unavailable=True, conclusion="logs_unavailable")
    return refresh_restart_log_evidence(job, bypass_cache=bypass_cache)


def _provider_command_state(job: Any | None) -> str:
    if job is None:
        return "unknown"
    from aethos_core.operational_skill_runtime.evidence_collector import resolve_command_state

    submitted, command_name = resolve_command_state(job)
    if submitted:
        return "submitted"
    params = getattr(job, "params", None) or {}
    exec_state = str(params.get("execution_state") or "")
    if exec_state == "execution_failed":
        return "failed"
    if command_name:
        return "submitted"
    return "unknown"


def _status_labels(thread: Any, job: Any | None) -> tuple[str, str]:
    status = str(getattr(thread, "status", None) or "unknown")
    if job is not None:
        params = getattr(job, "params", None) or {}
        exec_state = str(params.get("execution_state") or "")
        restart_state = str(params.get("restart_verification_state") or "")
        if exec_state:
            status = exec_state.replace("_", " ")
        verification = restart_state.replace("_", " ") if restart_state else "waiting for provider-side restart evidence"
        return status, verification
    return status.replace("_", " "), "waiting for provider-side restart evidence"
