# SPDX-License-Identifier: Apache-2.0
"""Rank memory candidates by semantic relevance, not recency alone."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class MemoryCandidate:
    source: str
    provider: str = ""
    service: str = ""
    operation: str = ""
    score: float = 0.0
    execution_job_id: str = ""
    thread: Any | None = None
    execution_job: Any | None = None
    target: Any | None = None
    meta: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "provider": self.provider,
            "service": self.service,
            "operation": self.operation,
            "score": round(self.score, 3),
            "execution_job_id": self.execution_job_id,
            "meta": dict(self.meta),
        }


def rank_memory_candidates(
    *,
    session_id: str,
    user_text: str,
    service_phrase: str = "",
) -> list[MemoryCandidate]:
    from aethos_core.aethos_identity.context_reconstructor import search_provider_targets
    from aethos_core.continuity_intelligence.continuity_timeline import build_continuity_timeline
    from aethos_core.continuity_intelligence.operational_focus_model import get_operational_focus
    from aethos_core.operational_thread_memory.mutation_thread_memory import find_execution_job_for_service
    from aethos_core.operational_thread_memory.thread_persistence import get_active_thread, is_thread_expired, load_thread_state
    from aethos_core.runtime.jobs import job_store

    phrase = (service_phrase or "").strip().lower()
    lower = (user_text or "").lower()
    candidates: list[MemoryCandidate] = []

    active = get_active_thread(session_id=session_id)
    if active is not None and not is_thread_expired(active):
        score = _score_thread(active, phrase=phrase)
        candidates.append(
            MemoryCandidate(
                source="active_operational_thread",
                provider=str(active.provider or ""),
                service=str(active.service or ""),
                operation=str(active.operation or ""),
                score=score,
                execution_job_id=str(active.execution_job_id or ""),
                thread=active,
            )
        )

    stale = load_thread_state(session_id=session_id)
    if stale is not None and stale is not active:
        score = _score_thread(stale, phrase=phrase, stale=True)
        if score > 0.2:
            candidates.append(
                MemoryCandidate(
                    source="expired_operational_thread",
                    provider=str(stale.provider or ""),
                    service=str(stale.service or ""),
                    operation=str(stale.operation or ""),
                    score=score,
                    execution_job_id=str(stale.execution_job_id or ""),
                    thread=stale,
                )
            )

    if phrase:
        job = find_execution_job_for_service(session_id=session_id, service_phrase=phrase)
        if job is not None:
            params = getattr(job, "params", None) or {}
            candidates.append(
                MemoryCandidate(
                    source="semantic_execution_job",
                    provider=str(params.get("provider") or "railway"),
                    service=str(params.get("target_name") or phrase),
                    operation=str(params.get("operation_type") or ""),
                    score=0.95 if _matches(phrase, str(params.get("target_name") or "")) else 0.7,
                    execution_job_id=str(getattr(job, "id", "") or ""),
                    execution_job=job,
                )
            )

    for row in reversed(job_store.list_all()):
        if str(getattr(row, "session_id", "") or "") != session_id:
            continue
        if row.job_type not in {"mutation_execution", "mutation_preflight"}:
            continue
        params = getattr(row, "params", None) or {}
        service = str(params.get("target_name") or (params.get("target") or {}).get("service_name") or "")
        if phrase and not _matches(phrase, service):
            continue
        if not phrase and not service:
            continue
        score = 0.55 if phrase else 0.35
        if phrase and _matches(phrase, service):
            score = 0.88
        candidates.append(
            MemoryCandidate(
                source="recent_operational_timeline",
                provider=str(params.get("provider") or "railway"),
                service=service,
                operation=str(params.get("operation_type") or ""),
                score=score,
                execution_job_id=str(getattr(row, "id", "") or "") if row.job_type == "mutation_execution" else "",
                execution_job=row if row.job_type == "mutation_execution" else None,
            )
        )

    focus = get_operational_focus(session_id=session_id)
    if focus.get("service"):
        score = 0.72
        if phrase and _matches(phrase, str(focus.get("service") or "")):
            score = 0.93
        elif phrase:
            score = 0.15
        candidates.append(
            MemoryCandidate(
                source="operational_focus",
                provider=str(focus.get("provider") or ""),
                service=str(focus.get("service") or ""),
                operation=str(focus.get("operation") or ""),
                score=score,
                execution_job_id=str(focus.get("execution_job_id") or ""),
            )
        )

    if phrase:
        topology = search_provider_targets(phrase)
        if topology.resolved:
            target = topology.resolved
            candidates.append(
                MemoryCandidate(
                    source="topology_match",
                    provider=target.provider,
                    service=target.service_name,
                    operation="inspect",
                    score=0.42 if phrase else 0.2,
                    target=target,
                )
            )

    for entry in build_continuity_timeline(session_id=session_id):
        if phrase and not _matches(phrase, entry.service):
            continue
        score = entry.conversation_focus_score * (0.95 if phrase and _matches(phrase, entry.service) else 0.5)
        candidates.append(
            MemoryCandidate(
                source="timeline_entry",
                provider=entry.provider,
                service=entry.service,
                operation=entry.operation,
                score=score,
                execution_job_id=entry.execution_job_id,
                meta={"detail": entry.detail},
            )
        )

    from aethos_core.aethos_identity.context_reconstructor import _is_plausible_service_phrase

    if phrase and _is_plausible_service_phrase(phrase):
        for candidate in list(candidates):
            if candidate.service and not _matches(phrase, candidate.service):
                candidate.score -= 0.45
    elif not phrase or not _is_plausible_service_phrase(phrase):
        for candidate in candidates:
            if candidate.source in {"operational_focus", "recent_operational_timeline", "timeline_entry", "semantic_execution_job"}:
                candidate.score += 0.12

    deduped: dict[str, MemoryCandidate] = {}
    for candidate in candidates:
        if candidate.execution_job is None and candidate.execution_job_id:
            from aethos_core.runtime.jobs import job_store

            candidate.execution_job = job_store.get(candidate.execution_job_id)
        key = f"{candidate.source}:{candidate.provider}:{candidate.service}:{candidate.execution_job_id}"
        existing = deduped.get(key)
        if existing is None or candidate.score > existing.score:
            deduped[key] = candidate

    ranked = sorted(deduped.values(), key=lambda c: c.score, reverse=True)
    return ranked


def best_memory_candidate(*, session_id: str, user_text: str, service_phrase: str = "") -> MemoryCandidate | None:
    ranked = rank_memory_candidates(session_id=session_id, user_text=user_text, service_phrase=service_phrase)
    if not ranked:
        return None
    if ranked[0].score < 0.25:
        return None
    return ranked[0]


def _score_thread(thread: Any, *, phrase: str, stale: bool = False) -> float:
    service = str(getattr(thread, "service", "") or "")
    score = 0.82 if not stale else 0.62
    if phrase and _matches(phrase, service):
        score = 0.96 if not stale else 0.84
    elif phrase:
        score = 0.18
    return score


def _matches(phrase: str, service: str) -> bool:
    p = (phrase or "").strip().lower()
    s = (service or "").strip().lower()
    if not p or not s:
        return False
    return p == s or p in s or s in p
