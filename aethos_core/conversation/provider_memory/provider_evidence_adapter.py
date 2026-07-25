# SPDX-License-Identifier: Apache-2.0
"""Provider-generic evidence adapter contract for operational follow-ups."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class OperationStatus:
    execution_job_id: str = ""
    provider_command: str = "unknown"
    restart_evidence: str = "not detected"
    latest_log_timestamp: str | None = None
    service_health: str = "unknown"
    status_label: str = "unknown"
    verification_label: str = "waiting for provider-side evidence"

    def to_dict(self) -> dict[str, Any]:
        return {
            "execution_job_id": self.execution_job_id,
            "provider_command": self.provider_command,
            "restart_evidence": self.restart_evidence,
            "latest_log_timestamp": self.latest_log_timestamp,
            "service_health": self.service_health,
            "status_label": self.status_label,
            "verification_label": self.verification_label,
        }


@dataclass
class OperationVerification:
    conclusion: str = "inconclusive"
    verified: bool = False
    approval_time: str | None = None
    latest_log_timestamp: str | None = None
    startup_after_approval: bool = False
    timestamp_after_approval: bool = False
    timestamps_available: bool = False
    logs_unavailable: bool = False
    service_health: str = "unknown"
    provider_command: str = "unknown"
    evidence: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "conclusion": self.conclusion,
            "verified": self.verified,
            "approval_time": self.approval_time,
            "latest_log_timestamp": self.latest_log_timestamp,
            "startup_after_approval": self.startup_after_approval,
            "timestamp_after_approval": self.timestamp_after_approval,
            "timestamps_available": self.timestamps_available,
            "logs_unavailable": self.logs_unavailable,
            "service_health": self.service_health,
            "provider_command": self.provider_command,
            "evidence": dict(self.evidence),
        }


@dataclass
class ProviderLogEntry:
    timestamp: str | None
    level: str
    message: str

    def to_dict(self) -> dict[str, Any]:
        return {"timestamp": self.timestamp, "level": self.level, "message": self.message}


class ProviderEvidenceAdapter(ABC):
    provider: str

    @abstractmethod
    def get_operation_status(self, thread: Any, job: Any | None) -> OperationStatus: ...

    @abstractmethod
    def get_latest_logs(
        self,
        thread: Any,
        job: Any | None,
        *,
        limit: int = 5,
        level_filter: str | None = None,
    ) -> list[ProviderLogEntry]: ...

    @abstractmethod
    def verify_operation(self, thread: Any, job: Any | None) -> OperationVerification: ...

    @abstractmethod
    def explain_failure(self, thread: Any, job: Any | None) -> str: ...

    def watch_until_done(self, thread: Any, job: Any | None, *, session_id: str) -> bool:
        from aethos_core.operational_thread_memory.completion_watch import create_completion_watch

        job_id = str(getattr(job, "id", "") or getattr(thread, "execution_job_id", "") or "unknown")
        create_completion_watch(
            session_id=session_id,
            provider=str(getattr(thread, "provider", "") or self.provider),
            project=str(getattr(thread, "project", "") or ""),
            environment=str(getattr(thread, "environment", "") or "production"),
            service=str(getattr(thread, "service", "") or ""),
            operation=str(getattr(thread, "operation", "") or "restart"),
            execution_job_id=job_id,
        )
        return True

    def capability_gap_message(self, thread: Any, *, action: str) -> str:
        path = thread.service_path() if hasattr(thread, "service_path") else str(getattr(thread, "service", "unknown"))
        return (
            f"I still have the active **{self.provider}** thread for **{path}**, "
            f"but **{self.provider}** follow-up `{action}` is not implemented yet.\n\n"
            f"I can only report stored execution state until the {self.provider} evidence adapter is wired."
        )


def load_evidence_adapter(provider: str) -> ProviderEvidenceAdapter | None:
    provider = (provider or "").strip().lower()
    if provider == "railway":
        from aethos_core.conversation.provider_memory.adapters.railway_adapter import RailwayEvidenceAdapter

        return RailwayEvidenceAdapter()
    if provider == "vercel":
        from aethos_core.conversation.provider_memory.adapters.vercel_adapter import VercelEvidenceAdapter

        return VercelEvidenceAdapter()
    if provider == "github":
        from aethos_core.conversation.provider_memory.adapters.github_adapter import GitHubEvidenceAdapter

        return GitHubEvidenceAdapter()
    if provider in {"aws", "docker", "kubernetes", "k8s"}:
        from aethos_core.conversation.provider_memory.adapters.stub_adapter import StubEvidenceAdapter

        return StubEvidenceAdapter(provider=provider if provider != "k8s" else "kubernetes")
    return None
