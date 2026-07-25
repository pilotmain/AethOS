# SPDX-License-Identifier: Apache-2.0
"""Semantic operational intent interpretation."""

from __future__ import annotations

from dataclasses import dataclass

from aethos_core.operational_cognition.cognition_memory_bridge import CognitionMemoryContext


@dataclass
class OperationalIntentDecision:
    intent: str
    provider: str | None
    target: str | None
    confidence: float
    signals: list[str]


def interpret_operational_intent(
    text: str,
    *,
    session_id: str = "default",
    memory: CognitionMemoryContext | None = None,
) -> OperationalIntentDecision:
    raw = (text or "").strip()
    mem = memory
    if mem is None:
        from aethos_core.operational_cognition.cognition_memory_bridge import load_cognition_memory

        mem = load_cognition_memory(session_id=session_id)

    from aethos_core.chat.route_trace import is_internal_diagnostics_query
    from aethos_core.failed_service_investigation.global_preemption import (
        classify_failed_service_intent,
        should_preempt_to_failed_service,
    )
    from aethos_core.operational_planner.query_planner import plan_operational_query
    from aethos_core.response_composition.response_intent_classifier import classify_response_intent

    if is_internal_diagnostics_query(raw):
        return OperationalIntentDecision(
            intent="inspect_route_trace",
            provider=None,
            target=None,
            confidence=0.95,
            signals=["internal_diagnostics"],
        )

    failed_intent = classify_failed_service_intent(raw)
    if should_preempt_to_failed_service(raw, session_id=session_id):
        mapped = _map_failed_intent(failed_intent)
        target = _extract_target_from_memory_or_text(raw, session_id=session_id, memory=mem)
        return OperationalIntentDecision(
            intent=mapped,
            provider="railway",
            target=target,
            confidence=0.93 if failed_intent != "none" else 0.82,
            signals=["failed_service_preemption", failed_intent],
        )

    response_intent = classify_response_intent(raw, session_id=session_id)
    if response_intent.kind in {"filter", "format", "rerender"} and mem.has_render_context:
        return OperationalIntentDecision(
            intent="transform_response",
            provider=str(mem.health_provider or None),
            target=None,
            confidence=0.9,
            signals=[response_intent.kind, response_intent.output_format or "", response_intent.filter_mode or ""],
        )

    plan = plan_operational_query(raw, session_id=session_id)
    if plan.action_type in {"provider_wide_readonly", "provider_readonly"}:
        return OperationalIntentDecision(
            intent="inventory_health_report" if plan.intent == "inventory_health_report" else plan.intent,
            provider=plan.provider,
            target=plan.target,
            confidence=0.88,
            signals=["provider_wide_planner", plan.scope, plan.action_type],
        )

    if plan.action_type == "mutation":
        return OperationalIntentDecision(
            intent="mutation",
            provider=plan.provider,
            target=plan.target,
            confidence=0.85,
            signals=["explicit_mutation", plan.scope],
        )

    if plan.action_type == "active_followup":
        return OperationalIntentDecision(
            intent=plan.intent,
            provider=plan.provider or mem.active_provider or None,
            target=plan.target or mem.active_service or None,
            confidence=0.8,
            signals=["active_followup", plan.intent],
        )

    return OperationalIntentDecision(
        intent=plan.intent if plan.intent != "unknown" else "general_operational",
        provider=plan.provider,
        target=plan.target,
        confidence=0.55,
        signals=["planner_fallback", plan.scope],
    )


def _map_failed_intent(failed_intent: str) -> str:
    mapping = {
        "why_failed": "diagnose_failure",
        "show_logs": "fetch_logs",
        "show_error_logs": "fetch_logs",
        "inspect_events": "fetch_events",
        "create_fix_plan": "create_fix_plan",
        "what_should_i_fix": "create_fix_plan",
        "retry_check": "verify_operation",
        "status": "health_check",
    }
    return mapping.get(failed_intent, "diagnose_failure")


def _extract_target_from_memory_or_text(
    text: str,
    *,
    session_id: str,
    memory: CognitionMemoryContext,
) -> str | None:
    from aethos_core.failed_service_investigation.global_preemption import detect_failed_service_reference

    ref = detect_failed_service_reference(text, session_id=session_id)
    if ref and ref.rows:
        row = ref.rows[0]
        project = str(row.get("project") or "")
        service = str(row.get("service") or "")
        if project and service:
            return f"{project}/{service}"
        return service or project or None
    if memory.active_service:
        return memory.active_service
    return None
