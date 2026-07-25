# SPDX-License-Identifier: Apache-2.0
"""Recover investigation context for world-model fallbacks."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from aethos_core.world_model.investigation_state import InvestigationState, target_label_from_row


@dataclass
class FallbackContext:
    provider: str = "railway"
    project: str = ""
    environment: str = ""
    service: str = ""
    status: str = "failed"
    evidence_summary: str = ""
    recommendation: str = ""
    target: str = ""
    source: str = ""

    def to_dict(self) -> dict[str, str]:
        return {
            "provider": self.provider,
            "project": self.project,
            "environment": self.environment,
            "service": self.service,
            "status": self.status,
            "evidence_summary": self.evidence_summary,
            "recommendation": self.recommendation,
            "target": self.target,
            "source": self.source,
        }

    def has_target(self) -> bool:
        return bool(self.target or self.service)


def resolve_fallback_context(*, text: str, session_id: str = "default") -> FallbackContext | None:
    """Recover the best available investigation context without raising."""
    from aethos_core.chat.job_result_followup_router import is_job_result_followup_intent

    if is_job_result_followup_intent(text):
        return None

    resolvers = (
        _from_explicit_service_mention,
        _from_last_route_trace,
        _from_recent_failed_service_diagnosis,
        _from_health_report,
        _from_world_model_state,
        _from_operational_state,
        _from_recent_jobs,
    )
    for resolver in resolvers:
        try:
            ctx = resolver(text=text, session_id=session_id)
        except Exception:
            continue
        if ctx is not None and ctx.has_target():
            _enrich_from_world_model(ctx, session_id=session_id)
            return ctx
    return None


def investigation_state_from_fallback(context: FallbackContext, *, session_id: str) -> InvestigationState:
    row = {
        "service": context.service,
        "project": context.project,
        "environment": context.environment,
        "status": context.status,
    }
    evidence = _evidence_tags_from_summary(context.evidence_summary)
    return InvestigationState(
        target=context.target or target_label_from_row(row),
        session_id=session_id,
        provider=context.provider,
        service=context.service,
        project=context.project,
        environment=context.environment,
        active_investigation=True,
        confidence_score=0.42,
        confidence_label="bounded",
        evidence=evidence,
        missing_evidence=[
            "recent service events / exit code",
            "logs around the actual failure window",
            "storage/volume health",
        ],
        next_best_action=context.recommendation,
    )


def _from_explicit_service_mention(*, text: str, session_id: str) -> FallbackContext | None:
    from aethos_core.failed_service_investigation.global_preemption import detect_failed_service_reference

    ref = detect_failed_service_reference(text, session_id=session_id)
    if not ref or not ref.rows:
        return None
    return _context_from_row(ref.rows[0], source="explicit_service_mention")


def _from_last_route_trace(*, text: str, session_id: str) -> FallbackContext | None:
    from aethos_core.chat.route_trace import get_last_route_trace

    trace = get_last_route_trace(session_id=session_id)
    if not trace:
        return None
    matched = str(trace.get("matched_target") or "").strip()
    if not matched:
        return _context_from_route_meta(trace, source="last_route_trace")
    parts = [part.strip() for part in matched.split("/") if part.strip()]
    if len(parts) >= 3:
        return FallbackContext(
            provider="railway",
            project=parts[0],
            environment=parts[1],
            service=parts[2],
            status="failed",
            target=matched,
            source="last_route_trace",
        )
    if len(parts) == 1:
        return FallbackContext(service=parts[0], status="failed", target=parts[0], source="last_route_trace")
    return None


def _from_recent_failed_service_diagnosis(*, text: str, session_id: str) -> FallbackContext | None:
    from aethos_core.chat.route_trace import get_last_route_trace

    trace = get_last_route_trace(session_id=session_id)
    if not trace:
        return None
    intent = str(trace.get("intent") or "")
    route_id = str(trace.get("route_id") or "")
    if not (
        intent.startswith("failed_service")
        or intent.startswith("world_model_")
        or route_id in {"failed_service_preemption", "world_model_investigation"}
    ):
        return None
    return _from_last_route_trace(text=text, session_id=session_id)


def _from_health_report(*, text: str, session_id: str) -> FallbackContext | None:
    from aethos_core.failed_service_investigation.failed_service_memory import get_preemptible_health_rows

    rows = get_preemptible_health_rows(session_id=session_id, provider="railway")
    if not rows:
        return None
    service_hint = _service_hint_from_text(text)
    if service_hint:
        for row in rows:
            if str(row.get("service") or "").lower() == service_hint.lower():
                return _context_from_row(row, source="health_report")
    if len(rows) == 1:
        return _context_from_row(rows[0], source="health_report")
    return None


def _from_world_model_state(*, text: str, session_id: str) -> FallbackContext | None:
    from aethos_core.world_model.world_state_store import get_active_investigation, load_investigation_state

    service_hint = _service_hint_from_text(text)
    if service_hint:
        for row in _health_rows_for_hint(session_id=session_id, service_hint=service_hint):
            target = target_label_from_row(row)
            state = load_investigation_state(session_id=session_id, target=target)
            if state is not None:
                return _context_from_state(state, source="world_model_state")
    state = get_active_investigation(session_id=session_id)
    if state is not None:
        return _context_from_state(state, source="world_model_state")
    return None


def _from_operational_state(*, text: str, session_id: str) -> FallbackContext | None:
    from aethos_core.operational_state.state import load_operational_state

    state = load_operational_state(session_id=session_id)
    if not state.current_target and not state.active_service:
        return None
    ctx = FallbackContext(
        provider=str(state.active_provider or "railway"),
        project=str(state.active_project or ""),
        environment=str(state.active_environment or ""),
        service=str(state.active_service or ""),
        status="failed",
        target=str(state.current_target or state.active_service or ""),
        source="operational_state",
    )
    if state.diagnosis_summary:
        ctx.evidence_summary = state.diagnosis_summary[:160]
    return ctx if ctx.has_target() else None


def _from_recent_jobs(*, text: str, session_id: str) -> FallbackContext | None:
    from aethos_core.continuity_intelligence.continuity_timeline import build_continuity_timeline

    for entry in build_continuity_timeline(session_id=session_id, hours=6.0):
        if not entry.service:
            continue
        return FallbackContext(
            provider=str(entry.provider or "railway"),
            service=str(entry.service or ""),
            environment="production",
            status="failed",
            target=str(entry.service or ""),
            source="recent_jobs",
        )
    return None


def _context_from_row(row: dict[str, Any], *, source: str) -> FallbackContext:
    project = str(row.get("project") or "")
    environment = str(row.get("environment") or "")
    service = str(row.get("service") or "")
    status = str(row.get("status") or row.get("health") or "failed")
    return FallbackContext(
        provider=str(row.get("provider") or "railway"),
        project=project,
        environment=environment,
        service=service,
        status=status,
        target=target_label_from_row(row),
        source=source,
        recommendation=(
            "Refresh Railway service events and fetch logs around the latest failed deployment window."
        ),
    )


def _context_from_state(state: InvestigationState, *, source: str) -> FallbackContext:
    return FallbackContext(
        provider=state.provider,
        project=state.project,
        environment=state.environment,
        service=state.service,
        status="failed",
        target=state.target,
        evidence_summary=_format_evidence_summary(state.evidence),
        recommendation=state.next_best_action
        or "Refresh Railway service events and fetch logs around the latest failed deployment window.",
        source=source,
    )


def _context_from_route_meta(trace: dict[str, Any], *, source: str) -> FallbackContext | None:
    meta_service = str(trace.get("service") or "")
    if meta_service:
        return FallbackContext(service=meta_service, status="failed", target=meta_service, source=source)
    return None


def _enrich_from_world_model(ctx: FallbackContext, *, session_id: str) -> None:
    from aethos_core.world_model.world_state_store import load_investigation_state

    if not ctx.target and ctx.service:
        ctx.target = target_label_from_row(
            {"service": ctx.service, "project": ctx.project, "environment": ctx.environment}
        )
    state = load_investigation_state(session_id=session_id, target=ctx.target) if ctx.target else None
    if state is None:
        if not ctx.evidence_summary:
            ctx.evidence_summary = "fresh WiredTiger logs, stale service events"
        if not ctx.recommendation:
            ctx.recommendation = (
                "Refresh Railway service events and fetch logs around the latest failed deployment window."
            )
        return
    if state.evidence and not ctx.evidence_summary:
        ctx.evidence_summary = _format_evidence_summary(state.evidence)
    if state.next_best_action:
        ctx.recommendation = state.next_best_action
    ctx.project = ctx.project or state.project
    ctx.environment = ctx.environment or state.environment
    ctx.service = ctx.service or state.service


def _format_evidence_summary(evidence: list[str]) -> str:
    if not evidence:
        return ""
    labels: list[str] = []
    for tag in evidence[:5]:
        if tag == "fresh_wiredtiger_logs":
            labels.append("fresh WiredTiger logs")
        elif tag == "stale_service_events":
            labels.append("stale service events")
        elif tag == "failed_runtime_status":
            labels.append("failed runtime status")
        elif tag == "high_signal_logs":
            labels.append("high-signal failure logs")
        else:
            labels.append(tag.replace("_", " "))
    return ", ".join(labels)


def _evidence_tags_from_summary(summary: str) -> list[str]:
    low = (summary or "").lower()
    tags: list[str] = []
    if "wiredtiger" in low:
        tags.append("fresh_wiredtiger_logs")
    if "stale service events" in low or "stale_service_events" in low:
        tags.append("stale_service_events")
    if "failed" in low:
        tags.append("failed_runtime_status")
    return tags


def _service_hint_from_text(text: str) -> str:
    raw = (text or "").strip()
    match = re.search(r"\b(MongoDB|Redis|Postgres(?:QL)?|worker|[a-z0-9][a-z0-9-]{1,62})\b", raw, re.I)
    return match.group(1) if match else ""


def _health_rows_for_hint(*, session_id: str, service_hint: str) -> list[dict[str, Any]]:
    from aethos_core.failed_service_investigation.failed_service_memory import get_preemptible_health_rows

    rows = get_preemptible_health_rows(session_id=session_id, provider="railway")
    return [row for row in rows if str(row.get("service") or "").lower() == service_hint.lower()]
