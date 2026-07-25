# SPDX-License-Identifier: Apache-2.0
"""Chronological operational narrative for a session."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any


@dataclass
class TimelineEntry:
    timestamp: str
    provider: str = ""
    service: str = ""
    operation: str = ""
    result: str = ""
    source: str = ""
    execution_job_id: str = ""
    conversation_focus_score: float = 0.5
    detail: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "provider": self.provider,
            "service": self.service,
            "operation": self.operation,
            "result": self.result,
            "source": self.source,
            "execution_job_id": self.execution_job_id,
            "conversation_focus_score": self.conversation_focus_score,
            "detail": self.detail,
        }


def build_continuity_timeline(*, session_id: str, hours: float = 8.0) -> list[TimelineEntry]:
    from aethos_core.operational_thread_memory.thread_persistence import load_thread_state
    from aethos_core.runtime.jobs import job_store

    entries: list[TimelineEntry] = []
    cutoff = datetime.now(UTC) - timedelta(hours=hours)

    for row in job_store.list_all():
        if str(getattr(row, "session_id", "") or "") != session_id:
            continue
        ts = _job_timestamp(row)
        if ts and ts < cutoff:
            continue
        params = getattr(row, "params", None) or {}
        target = dict(params.get("target") or {})
        service = str(params.get("target_name") or target.get("service_name") or "")
        provider = str(params.get("provider") or "railway")
        operation = str(params.get("operation_type") or row.job_type or "")
        result = str(params.get("execution_state") or params.get("restart_verification_state") or getattr(row.status, "value", row.status) or "")
        detail = str(params.get("lifecycle_summary") or params.get("user_request") or row.title or "")
        score = 0.85 if row.job_type == "mutation_execution" else 0.65
        entries.append(
            TimelineEntry(
                timestamp=ts.isoformat() if ts else datetime.now(UTC).isoformat(),
                provider=provider,
                service=service,
                operation=operation,
                result=result,
                source="job",
                execution_job_id=str(getattr(row, "id", "") or ""),
                conversation_focus_score=score,
                detail=detail,
            )
        )

    thread = load_thread_state(session_id=session_id)
    if thread is not None:
        entries.append(
            TimelineEntry(
                timestamp=thread.updated_at or datetime.now(UTC).isoformat(),
                provider=str(thread.provider or ""),
                service=str(thread.service or ""),
                operation=str(thread.operation or ""),
                result=str(thread.status or ""),
                source="thread",
                execution_job_id=str(thread.execution_job_id or ""),
                conversation_focus_score=0.9,
                detail=str(thread.last_system_result or ""),
            )
        )

    entries.sort(key=lambda e: e.timestamp, reverse=True)
    return entries


def timeline_for_service(*, session_id: str, service_phrase: str, hours: float = 24.0) -> list[TimelineEntry]:
    norm = (service_phrase or "").strip().lower()
    return [
        entry
        for entry in build_continuity_timeline(session_id=session_id, hours=hours)
        if norm and (norm in entry.service.lower() or norm in entry.detail.lower())
    ]


def timeline_within_hours(*, session_id: str, hours: float) -> list[TimelineEntry]:
    cutoff = datetime.now(UTC) - timedelta(hours=hours)
    return [entry for entry in build_continuity_timeline(session_id=session_id, hours=max(hours, 8.0)) if _parse_ts(entry.timestamp) >= cutoff]


def summarize_timeline(entries: list[TimelineEntry], *, hours_label: str = "recent") -> str:
    if not entries:
        return f"I do not have stored operational timeline entries for the {hours_label} window in this session yet."

    services = []
    seen = set()
    for entry in entries:
        key = f"{entry.provider}:{entry.service}"
        if entry.service and key not in seen:
            seen.add(key)
            services.append(f"**{entry.service}** ({entry.provider} · {entry.operation or 'operation'})")

    lines = [
        f"Yes — over the {hours_label} operational window in this session, we were working on governed provider operations.",
        "",
        "Main focus areas:",
    ]
    for svc in services[:6]:
        lines.append(f"- {svc}")
    lines.append("")
    lines.append("Recent operational events:")
    for entry in entries[:8]:
        lines.append(
            f"- `{entry.timestamp}` · **{entry.service or 'unknown'}** · {entry.operation or 'operation'} · {entry.result or 'updated'}"
        )
    return "\n".join(lines)


def _job_timestamp(row: Any) -> datetime | None:
    for attr in ("updated_at", "created_at"):
        raw = getattr(row, attr, None)
        if raw is None:
            continue
        if isinstance(raw, (int, float)):
            return datetime.fromtimestamp(float(raw), tz=UTC)
        parsed = _parse_ts(str(raw))
        if parsed.year > 1971:
            return parsed
    return None


def _parse_ts(raw: str) -> datetime:
    try:
        dt = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
    except ValueError:
        return datetime.min.replace(tzinfo=UTC)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt
