# SPDX-License-Identifier: Apache-2.0
"""Route failed-service investigation before generic diagnostics."""

from __future__ import annotations

from aethos_core.failed_service_investigation.failed_service_diagnosis import (
    collect_failed_service_evidence,
    compose_diagnosis_reply,
    compose_events_reply,
    compose_logs_reply,
    compose_status_reply,
)
from aethos_core.failed_service_investigation.failed_service_fix_plan import compose_fix_plan_reply
from aethos_core.failed_service_investigation.failed_service_resolver import (
    InvestigationKind,
    resolve_failed_service_target,
)
from aethos_core.failed_service_investigation.fallback_discovery import (
    FallbackDiscoveryResult,
    extract_target_label,
    format_discovery_preamble,
    resolve_failed_service_with_fallback,
)
from aethos_core.failed_service_investigation.global_preemption import (
    FailedServiceIntent,
    classify_failed_service_intent,
    should_block_generic_diagnostics,
    should_preempt_to_failed_service,
)


def failed_service_router_can_handle(text: str, *, session_id: str = "default") -> bool:
    if not should_preempt_to_failed_service(text, session_id=session_id):
        return False
    resolution = resolve_failed_service_target(text, session_id=session_id)
    return resolution.ok or resolution.reason == "ambiguous_service"


def compose_failed_service_investigation_reply(
    text: str,
    *,
    session_id: str = "default",
    intent: FailedServiceIntent | None = None,
    kind: InvestigationKind | None = None,
) -> tuple[str, str, dict[str, str]] | None:
    from aethos_core.world_model.investigation_engine import try_world_model_followup

    world_model = try_world_model_followup(text, session_id=session_id)
    if world_model is not None:
        return world_model

    if not should_preempt_to_failed_service(text, session_id=session_id):
        return None

    resolved_intent = intent or classify_failed_service_intent(text)
    investigation_kind = kind or _intent_to_kind(resolved_intent)
    if investigation_kind == "none":
        investigation_kind = "why_failed"
        resolved_intent = "why_failed"

    resolution, discovery = resolve_failed_service_with_fallback(text, session_id=session_id, kind=investigation_kind)
    if not resolution.ok:
        failure = _compose_resolution_failure(resolution, discovery=discovery, text=text)
        if failure is not None:
            return failure
        return None

    assert resolution.target is not None
    target = resolution.target
    preamble = format_discovery_preamble(discovery=discovery, resolution=resolution)

    if investigation_kind == "fix_plan" or resolved_intent in {"create_fix_plan", "what_should_i_fix"}:
        body, plan = compose_fix_plan_reply(target, session_id=session_id)
        meta = _meta_from_target(target, kind="fix_plan", discovery=discovery, session_id=session_id)
        meta["requires_approval"] = "true"
        meta["proposed_operation"] = str(plan.get("proposed_operation") or "")
        return preamble + body, "failed_service_fix_plan", meta

    evidence = collect_failed_service_evidence(target)
    from aethos_core.world_model.investigation_engine import prepend_story_if_active, update_investigation_from_evidence

    state = update_investigation_from_evidence(
        session_id=session_id,
        evidence=evidence,
        investigation_kind=investigation_kind,
        operator_intent=resolved_intent,
    )

    if investigation_kind == "inspect_events" or resolved_intent == "inspect_events":
        body = prepend_story_if_active(
            compose_events_reply(evidence),
            session_id=session_id,
            target=target.row,
            action="events",
        )
        meta = _meta_from_target(target, kind="inspect_events", discovery=discovery, session_id=session_id, state=state)
        return preamble + body, "failed_service_events", meta

    if investigation_kind in {"check_logs"} or resolved_intent in {"show_logs", "show_error_logs"}:
        body = prepend_story_if_active(
            compose_logs_reply(evidence),
            session_id=session_id,
            target=target.row,
            action="logs",
        )
        meta = _meta_from_target(target, kind="check_logs", discovery=discovery, session_id=session_id, state=state)
        return preamble + body, "failed_service_logs", meta

    if investigation_kind == "status" or resolved_intent == "status":
        body = prepend_story_if_active(
            compose_status_reply(evidence),
            session_id=session_id,
            target=target.row,
            action="status",
        )
        meta = _meta_from_target(target, kind="status", discovery=discovery, session_id=session_id, state=state)
        return preamble + body, "failed_service_status", meta

    body = compose_diagnosis_reply(evidence, investigation_state=state)
    body = prepend_story_if_active(body, session_id=session_id, target=target.row, action="diagnosis")
    meta = _meta_from_target(target, kind="why_failed", discovery=discovery, session_id=session_id, state=state)
    return preamble + body, "failed_service_diagnosis", meta


def _intent_to_kind(intent: FailedServiceIntent) -> InvestigationKind:
    mapping: dict[str, InvestigationKind] = {
        "why_failed": "why_failed",
        "show_logs": "check_logs",
        "show_error_logs": "check_logs",
        "inspect_events": "inspect_events",
        "create_fix_plan": "fix_plan",
        "what_should_i_fix": "fix_plan",
        "retry_check": "why_failed",
        "status": "status",
    }
    return mapping.get(intent, "none")


def _meta_from_target(
    target,
    *,
    kind: str,
    discovery: FallbackDiscoveryResult | None = None,
    session_id: str = "default",
    state=None,
) -> dict[str, str]:
    row = target.row
    meta = {
        "provider": target.provider,
        "scope": "failed_service_investigation",
        "investigation_kind": kind,
        "service": str(row.get("service") or ""),
        "project": str(row.get("project") or ""),
        "environment": str(row.get("environment") or ""),
        "from_health_report": "true" if not (discovery and discovery.discovered) else "discovered",
        "active_thread_override": "true",
        "block_vercel_diagnostics": "true",
    }
    if discovery and discovery.discovered:
        meta["fallback_discovery"] = "true"
        meta["discovery_source"] = "railway_inventory_refresh"
    if state is not None:
        meta["world_model_active"] = "true"
        meta["confidence_score"] = f"{state.confidence_score:.2f}"
        meta["confidence_label"] = state.confidence_label
        meta["world_model_target"] = state.target
    return meta


def _compose_resolution_failure(
    resolution,
    *,
    discovery: FallbackDiscoveryResult | None = None,
    text: str = "",
) -> tuple[str, str, dict[str, str]] | None:
    if resolution.reason == "discovery_failed":
        target_label = extract_target_label(text)
        detail = ""
        if discovery and discovery.error:
            detail = f"\n\nDiscovery error: {discovery.error}"
        body = (
            f"I could not resolve **{target_label}** in Railway after refreshing inventory.{detail}\n\n"
            "Please run **check all services in railway** or tell me the exact project/service name."
        )
        return body, "failed_service_investigation_discovery_failed", {
            "from_health_report": "false",
            "fallback_discovery": "failed",
        }

    if resolution.reason == "missing_health_report":
        body = (
            "I'll refresh Railway inventory first, but I couldn't load provider-wide health yet.\n\n"
            "Please verify the Railway connection/token, then ask again or run **check all services in railway**."
        )
        return body, "failed_service_investigation_missing_report", {"from_health_report": "false"}

    if resolution.reason == "service_not_found":
        target_label = extract_target_label(text)
        if discovery and discovery.discovered:
            body = (
                f"I refreshed Railway inventory but couldn't match **{target_label}** to a service/project.\n\n"
                "Use the exact service or project name from Railway, or run **check all services in railway**."
            )
            return body, "failed_service_investigation_not_found", {
                "from_health_report": "discovered",
                "fallback_discovery": "true",
            }
        body = (
            "I couldn't match that service/resource to the last provider-wide Railway health report.\n\n"
            "Use the exact service or project name from the report, or ask **show only failed** first."
        )
        return body, "failed_service_investigation_not_found", {"from_health_report": "true"}

    if resolution.reason == "ambiguous_service" and resolution.candidates:
        lines = [
            "That name matches multiple Railway services in the last provider-wide health report.",
            "",
            "Which one did you mean?",
        ]
        for row in resolution.candidates[:6]:
            lines.append(
                f"- **{row.get('project', '—')} / {row.get('environment', '—')} / {row.get('service', '—')}**"
            )
        return "\n".join(lines), "failed_service_investigation_clarify", {"from_health_report": "true"}

    return None


__all__ = [
    "compose_failed_service_investigation_reply",
    "failed_service_router_can_handle",
    "should_block_generic_diagnostics",
    "should_preempt_to_failed_service",
]
