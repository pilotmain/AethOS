# SPDX-License-Identifier: Apache-2.0
"""Unified continuity recall — semantic ranking + reconstruction."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class RecallResult:
    confidence: float
    source: str
    provider: str = ""
    service: str = ""
    operation: str = ""
    execution_job_id: str = ""
    thread: Any | None = None
    execution_job: Any | None = None
    target: Any | None = None
    meta: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "confidence": round(self.confidence, 3),
            "source": self.source,
            "provider": self.provider,
            "service": self.service,
            "operation": self.operation,
            "execution_job_id": self.execution_job_id,
            "meta": dict(self.meta),
        }


def recall_operational_memory(*, session_id: str, user_text: str) -> RecallResult | None:
    from aethos_core.aethos_identity.context_reconstructor import extract_operational_resource_phrase
    from aethos_core.continuity_intelligence.operational_focus_model import record_from_thread
    from aethos_core.continuity_intelligence.semantic_memory_ranker import best_memory_candidate
    from aethos_core.operational_thread_memory.mutation_thread_memory import sync_thread_from_execution_job
    from aethos_core.operational_thread_memory.thread_persistence import save_thread_state
    from aethos_core.operational_thread_memory.thread_state import OperationalThreadState
    from aethos_core.operational_thread_memory.thread_persistence import _expires_at
    from datetime import UTC, datetime

    phrase = extract_operational_resource_phrase(user_text) or ""
    candidate = best_memory_candidate(session_id=session_id, user_text=user_text, service_phrase=phrase)
    if candidate is None:
        return None

    if candidate.thread is not None:
        record_from_thread(candidate.thread)
        return RecallResult(
            confidence=candidate.score,
            source=candidate.source,
            provider=candidate.provider,
            service=candidate.service,
            operation=candidate.operation,
            execution_job_id=candidate.execution_job_id,
            thread=candidate.thread,
            execution_job=candidate.execution_job,
            target=candidate.target,
            meta=dict(candidate.meta),
        )

    if candidate.execution_job is None and candidate.execution_job_id:
        from aethos_core.runtime.jobs import job_store

        candidate.execution_job = job_store.get(candidate.execution_job_id)

    if candidate.execution_job is not None:
        thread = sync_thread_from_execution_job(job=candidate.execution_job)
        record_from_thread(thread)
        return RecallResult(
            confidence=candidate.score,
            source=candidate.source,
            provider=candidate.provider,
            service=candidate.service,
            operation=candidate.operation,
            execution_job_id=str(getattr(candidate.execution_job, "id", "") or ""),
            thread=thread,
            execution_job=candidate.execution_job,
            meta=dict(candidate.meta),
        )

    if candidate.target is not None:
        target = candidate.target
        thread = OperationalThreadState(
            session_id=session_id,
            provider=target.provider,
            project=getattr(target, "project_name", None),
            environment=getattr(target, "environment", None) or "production",
            service=target.service_name,
            operation=candidate.operation or "inspect",
            status="reconstructed_from_topology",
            last_system_result=f"Reconstructed provider context for {getattr(target, 'path', target.service_name)}.",
            updated_at=datetime.now(UTC).isoformat(),
            expires_at=_expires_at(),
        )
        save_thread_state(thread)
        record_from_thread(thread)
        return RecallResult(
            confidence=candidate.score,
            source=candidate.source,
            provider=target.provider,
            service=target.service_name,
            operation=candidate.operation or "inspect",
            thread=thread,
            target=target,
            meta=dict(candidate.meta),
        )

    return RecallResult(
        confidence=candidate.score,
        source=candidate.source,
        provider=candidate.provider,
        service=candidate.service,
        operation=candidate.operation,
        execution_job_id=candidate.execution_job_id,
        meta=dict(candidate.meta),
    )


def apply_recall_to_session(*, session_id: str, user_text: str) -> RecallResult | None:
    return recall_operational_memory(session_id=session_id, user_text=user_text)
