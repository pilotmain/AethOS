# SPDX-License-Identifier: Apache-2.0
"""Honest capability-gap adapters for providers not yet wired."""

from __future__ import annotations

from typing import Any

from aethos_core.conversation.provider_memory.provider_evidence_adapter import (
    OperationStatus,
    OperationVerification,
    ProviderEvidenceAdapter,
    ProviderLogEntry,
)


class StubEvidenceAdapter(ProviderEvidenceAdapter):
    def __init__(self, *, provider: str) -> None:
        self.provider = provider

    def get_operation_status(self, thread: Any, job: Any | None) -> OperationStatus:
        return OperationStatus(
            execution_job_id=str(getattr(job, "id", "") or getattr(thread, "execution_job_id", "") or "unknown"),
            provider_command="unsupported",
            restart_evidence="not available",
            service_health="unknown",
            status_label=str(getattr(thread, "status", "unknown")),
            verification_label="provider adapter not implemented",
        )

    def get_latest_logs(
        self,
        thread: Any,
        job: Any | None,
        *,
        limit: int = 5,
        level_filter: str | None = None,
    ) -> list[ProviderLogEntry]:
        return []

    def verify_operation(self, thread: Any, job: Any | None) -> OperationVerification:
        return OperationVerification(
            conclusion="capability_gap",
            logs_unavailable=True,
            provider_command="unsupported",
            service_health="unknown",
        )

    def explain_failure(self, thread: Any, job: Any | None) -> str:
        path = thread.service_path() if hasattr(thread, "service_path") else str(getattr(thread, "service", "unknown"))
        return self.capability_gap_message(thread, action="explain_failure") + f"\n\nStored thread status: **{getattr(thread, 'status', 'unknown')}** for **{path}**."
