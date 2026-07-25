# SPDX-License-Identifier: Apache-2.0
"""Narrative operational continuity memory."""

from __future__ import annotations

import uuid
from typing import Any

_NARRATIVE: dict[str, list[str]] = {}


def append_operational_narrative(*, session_id: str, line: str, limit: int = 12) -> None:
    raw = (line or "").strip()
    if not raw:
        return
    bucket = _NARRATIVE.setdefault(session_id, [])
    bucket.append(raw)
    if len(bucket) > limit:
        del bucket[:-limit]


def load_recent_operational_narrative(*, session_id: str) -> list[str]:
    return list(_NARRATIVE.get(session_id) or [])


def clear_operational_narrative_for_tests() -> None:
    _NARRATIVE.clear()


def _is_continuity_recall_query(text: str) -> bool:
    raw = (text or "").strip().lower()
    return any(
        phrase in raw
        for phrase in (
            "what were we doing",
            "what were we working on",
            "what did we do earlier",
            "what were we doing earlier",
            "what were we doing last",
            "earlier with",
            "recap what we",
        )
    )


def compose_narrative_continuity_reply(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    if not _is_continuity_recall_query(text):
        return None
    return compose_resilient_continuity_reply(text, session_id=session_id)


def compose_resilient_continuity_reply(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]]:
    correlation_id = uuid.uuid4().hex[:8]
    lines = ["Earlier we were working on operational tasks.", ""]
    sources_loaded: list[str] = []
    sources_failed: list[str] = []
    partial_sections: list[str] = []

    state = _safe_load_state(session_id=session_id, sources_failed=sources_failed)
    if state is not None:
        sources_loaded.append("operational_state")
        if state.current_target or state.active_service:
            target = state.current_target or state.active_service or "the active service"
            provider = state.active_provider or state.provider_wide_provider or "the provider"
            partial_sections.append(f"- Focus: **{target}** on **{provider}**")
        elif state.provider_wide_provider:
            partial_sections.append(f"- Provider-wide health on **{state.provider_wide_provider}**")
            if state.failed_service_count:
                partial_sections.append(f"- Failed services in last report: **{state.failed_service_count}**")
        if state.diagnosis_summary:
            partial_sections.append(f"- {state.diagnosis_summary}")
        for item in state.recent_narrative[-5:]:
            partial_sections.append(f"- {item}")

    route_section = _safe_route_trace_section(session_id=session_id, sources_failed=sources_failed)
    if route_section:
        sources_loaded.append("route_trace")
        partial_sections.extend(route_section)

    job_section = _safe_recent_job_section(session_id=session_id, sources_failed=sources_failed)
    if job_section:
        sources_loaded.append("recent_jobs")
        partial_sections.extend(job_section)

    if partial_sections:
        lines.extend(["Recent confirmed context:"])
        lines.extend(partial_sections)
    else:
        lines.append("I don't have much stored operational narrative for this session yet.")

    if sources_failed:
        lines.extend(
            [
                "",
                "I could not load every memory source, but this is the reliable context I found.",
                f"(continuity correlation: `{correlation_id}` · partial sources: {', '.join(sources_loaded) or 'none'})",
            ]
        )

    meta = {
        "route_id": "operational_narrative_continuity",
        "matched_module": "operational_state.narrative",
        "continuity_correlation_id": correlation_id,
        "continuity_sources": ",".join(sources_loaded),
        "continuity_degraded": "true" if sources_failed else "false",
    }
    if state is not None:
        meta["operational_scope"] = state.operational_scope
    return "\n".join(lines), "operational_narrative_continuity", meta


def _safe_load_state(*, session_id: str, sources_failed: list[str]) -> Any:
    try:
        from aethos_core.operational_state.state import load_operational_state

        return load_operational_state(session_id=session_id)
    except Exception:
        sources_failed.append("operational_state")
        return None


def _safe_route_trace_section(*, session_id: str, sources_failed: list[str]) -> list[str]:
    try:
        from aethos_core.chat.route_trace import get_last_route_trace

        trace = get_last_route_trace(session_id=session_id)
        if not trace:
            return []
        route_id = str(trace.get("route_id") or "")
        matched_target = str(trace.get("matched_target") or "")
        route_trace = str(trace.get("route_trace") or "")
        rows: list[str] = []
        if route_id:
            rows.append(f"- Last route: **{route_id}**")
        if matched_target:
            rows.append(f"- Last matched target: **{matched_target}**")
        if route_trace:
            rows.append(f"- Route trace: `{route_trace}`")
        return rows
    except Exception:
        sources_failed.append("route_trace")
        return []


def _safe_recent_job_section(*, session_id: str, sources_failed: list[str]) -> list[str]:
    try:
        from aethos_core.runtime.jobs import job_store

        jobs = [job for job in job_store.list_all() if getattr(job, "session_id", "default") == session_id]
        if not jobs:
            return []
        rows = []
        for job in jobs[-3:]:
            rows.append(f"- Recent job `{job.id}`: **{job.title}** ({job.status})")
        return rows
    except Exception:
        sources_failed.append("recent_jobs")
        return []
