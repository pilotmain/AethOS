# SPDX-License-Identifier: Apache-2.0
"""Canonical operational runtime state — single source of truth."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from aethos_core.operational_cognition.cognition_memory_bridge import CognitionMemoryContext, load_cognition_memory


@dataclass
class OperationalState:
    session_id: str
    active_provider: str | None = None
    active_service: str | None = None
    active_project: str | None = None
    active_environment: str | None = None
    operational_scope: str = "unknown"
    current_intent: str | None = None
    current_target: str | None = None
    diagnosis_summary: str = ""
    evidence_state: str = "unknown"
    pending_approval: bool = False
    provider_wide_provider: str | None = None
    provider_wide_summary: dict[str, Any] = field(default_factory=dict)
    failed_service_count: int = 0
    recent_narrative: list[str] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "active_provider": self.active_provider,
            "active_service": self.active_service,
            "active_project": self.active_project,
            "active_environment": self.active_environment,
            "operational_scope": self.operational_scope,
            "current_intent": self.current_intent,
            "current_target": self.current_target,
            "diagnosis_summary": self.diagnosis_summary,
            "evidence_state": self.evidence_state,
            "pending_approval": self.pending_approval,
            "provider_wide_provider": self.provider_wide_provider,
            "provider_wide_summary": dict(self.provider_wide_summary),
            "failed_service_count": self.failed_service_count,
            "recent_narrative": list(self.recent_narrative),
            "meta": dict(self.meta),
        }


def load_operational_state(*, session_id: str = "default") -> OperationalState:
    memory: CognitionMemoryContext = load_cognition_memory(session_id=session_id)
    scope = "provider_wide" if memory.has_provider_wide_health else "unknown"
    if memory.has_active_thread:
        scope = "active_target"
    state = OperationalState(
        session_id=session_id,
        active_provider=memory.active_provider,
        active_service=memory.active_service,
        active_project=memory.active_project,
        active_environment=memory.active_environment,
        operational_scope=scope,
        provider_wide_provider=memory.health_provider,
        provider_wide_summary=dict(memory.health_summary),
        failed_service_count=memory.failed_service_count,
        meta={
            "has_render_context": memory.has_render_context,
            "last_output_format": memory.last_output_format,
            "last_filter_mode": memory.last_filter_mode,
        },
    )
    from aethos_core.operational_state.narrative import load_recent_operational_narrative

    state.recent_narrative = load_recent_operational_narrative(session_id=session_id)
    return state


def update_operational_state(
    *,
    session_id: str,
    intent: str | None = None,
    target: str | None = None,
    provider: str | None = None,
    diagnosis_summary: str = "",
    evidence_state: str = "",
    narrative_line: str = "",
) -> OperationalState:
    state = load_operational_state(session_id=session_id)
    if intent:
        state.current_intent = intent
    if target:
        state.current_target = target
    if provider:
        state.active_provider = provider
    if diagnosis_summary:
        state.diagnosis_summary = diagnosis_summary
    if evidence_state:
        state.evidence_state = evidence_state
    if narrative_line:
        from aethos_core.operational_state.narrative import append_operational_narrative

        append_operational_narrative(session_id=session_id, line=narrative_line)
        state.recent_narrative.append(narrative_line)
    return state
