# SPDX-License-Identifier: Apache-2.0
"""Unified operational memory bridge — single read authority."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class CognitionMemoryContext:
    session_id: str
    has_active_thread: bool = False
    active_provider: str = ""
    active_service: str = ""
    active_project: str = ""
    active_environment: str = "production"
    active_operation: str = ""
    has_provider_wide_health: bool = False
    health_provider: str = ""
    health_summary: dict[str, Any] = field(default_factory=dict)
    failed_service_count: int = 0
    has_render_context: bool = False
    last_output_format: str = ""
    last_filter_mode: str = "all"
    has_route_trace: bool = False
    reasoning_notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "has_active_thread": self.has_active_thread,
            "active_provider": self.active_provider,
            "active_service": self.active_service,
            "active_project": self.active_project,
            "active_environment": self.active_environment,
            "active_operation": self.active_operation,
            "has_provider_wide_health": self.has_provider_wide_health,
            "health_provider": self.health_provider,
            "health_summary": dict(self.health_summary),
            "failed_service_count": self.failed_service_count,
            "has_render_context": self.has_render_context,
            "last_output_format": self.last_output_format,
            "last_filter_mode": self.last_filter_mode,
            "has_route_trace": self.has_route_trace,
            "reasoning_notes": list(self.reasoning_notes),
        }


def load_cognition_memory(*, session_id: str = "default") -> CognitionMemoryContext:
    session_id = (session_id or "default").strip()
    ctx = CognitionMemoryContext(session_id=session_id)

    from aethos_core.operational_thread_memory.thread_persistence import get_active_thread

    thread = get_active_thread(session_id=session_id)
    if thread is not None:
        ctx.has_active_thread = True
        ctx.active_provider = str(getattr(thread, "provider", "") or "")
        ctx.active_service = str(getattr(thread, "service", "") or "")
        ctx.active_project = str(getattr(thread, "project", "") or "")
        ctx.active_environment = str(getattr(thread, "environment", "") or "production")
        ctx.active_operation = str(getattr(thread, "operation", "") or "")
        ctx.reasoning_notes.append("active_thread_available")

    from aethos_core.failed_service_investigation.failed_service_memory import (
        get_failed_health_rows,
        get_health_report_meta,
    )

    health_meta = get_health_report_meta(session_id=session_id)
    if health_meta.get("has_report"):
        ctx.has_provider_wide_health = True
        ctx.health_provider = str(health_meta.get("provider") or "railway")
        ctx.health_summary = dict(health_meta.get("summary") or {})
        ctx.failed_service_count = len(get_failed_health_rows(session_id=session_id))
        ctx.reasoning_notes.append("provider_wide_health_cached")

    from aethos_core.response_composition.response_memory import get_response_context

    render_ctx = get_response_context(session_id=session_id)
    if render_ctx.get("has_result"):
        ctx.has_render_context = True
        ctx.last_output_format = str(render_ctx.get("last_output_format") or "")
        ctx.last_filter_mode = str(render_ctx.get("last_filter_mode") or "all")
        ctx.reasoning_notes.append("render_context_available")

    from aethos_core.chat.route_trace import get_last_route_trace

    if get_last_route_trace(session_id=session_id):
        ctx.has_route_trace = True

    return ctx
