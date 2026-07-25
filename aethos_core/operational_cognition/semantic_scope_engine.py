# SPDX-License-Identifier: Apache-2.0
"""Semantic scope resolution — active thread is context, not prison."""

from __future__ import annotations

from dataclasses import dataclass

from aethos_core.operational_cognition.cognition_memory_bridge import CognitionMemoryContext


@dataclass
class SemanticScopeDecision:
    scope: str
    overrides_active_thread: bool
    reason: str


def resolve_semantic_scope(
    text: str,
    *,
    session_id: str = "default",
    memory: CognitionMemoryContext | None = None,
) -> SemanticScopeDecision:
    from aethos_core.operational_planner.query_planner import plan_operational_query
    from aethos_core.chat.route_trace import is_internal_diagnostics_query
    from aethos_core.failed_service_investigation.global_preemption import (
        classify_failed_service_intent,
        should_preempt_to_failed_service,
    )
    from aethos_core.response_composition.response_intent_classifier import classify_response_intent

    raw = (text or "").strip()
    mem = memory or __import__(
        "aethos_core.operational_cognition.cognition_memory_bridge",
        fromlist=["load_cognition_memory"],
    ).load_cognition_memory(session_id=session_id)

    if is_internal_diagnostics_query(raw):
        return SemanticScopeDecision(scope="identity", overrides_active_thread=True, reason="internal_diagnostics")

    if should_preempt_to_failed_service(raw, session_id=session_id):
        return SemanticScopeDecision(
            scope="provider_service",
            overrides_active_thread=True,
            reason="cached_failed_service_reference",
        )

    plan = plan_operational_query(raw, session_id=session_id)
    if plan.overrides_active_thread:
        return SemanticScopeDecision(
            scope=plan.scope,
            overrides_active_thread=True,
            reason="provider_wide_or_workspace_scope",
        )

    response_intent = classify_response_intent(raw, session_id=session_id)
    if response_intent.kind in {"filter", "format", "rerender"} and mem.has_render_context:
        return SemanticScopeDecision(scope="formatting", overrides_active_thread=True, reason="semantic_render_transform")

    failed_intent = classify_failed_service_intent(raw)
    if failed_intent != "none" and mem.has_provider_wide_health:
        return SemanticScopeDecision(scope="provider_service", overrides_active_thread=True, reason="failed_service_intent")

    if mem.has_active_thread and not plan.overrides_active_thread:
        return SemanticScopeDecision(scope="active_target", overrides_active_thread=False, reason="inherit_active_thread")

    return SemanticScopeDecision(scope=plan.scope, overrides_active_thread=plan.overrides_active_thread, reason="planner_scope")
