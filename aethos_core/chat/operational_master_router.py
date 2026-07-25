# SPDX-License-Identifier: Apache-2.0
"""Single operational routing authority for all chat transports."""

from __future__ import annotations

import logging
from contextvars import ContextVar
from dataclasses import dataclass, field

_log = logging.getLogger(__name__)

_in_master_route: ContextVar[bool] = ContextVar("_in_master_route", default=False)

ROUTES_BEFORE_READONLY_DIAGNOSTICS = frozenset(
    {
        "identity_contract",
        "internal_diagnostics",
        "world_model_investigation",
        "explicit_mutation",
        "provider_wide_planner",
        "failed_service_preemption",
        "source_binding_correction",
        "pending_action_continuation",
        "task_continuation",
        "retry_active_operation",
        "provider_followup",
        "active_thread_followup",
    }
)

BLOCKED_WHEN_PRIORITY = frozenset(
    {
        "vercel_why_down",
        "vercel_readonly",
        "browser_diagnostic",
        "generic_fix_plan",
        "continuity_reconstruction",
        "operation_preflight",
    }
)


@dataclass
class OperationalRouteDecision:
    reply: str
    intent: str
    meta: dict[str, str]
    route_id: str
    matched_module: str
    blocked_routes: list[str] = field(default_factory=list)
    matched_target: str = ""
    trace_chain: list[str] = field(default_factory=list)


def _pack(
    handled: tuple[str, str, dict[str, str]],
    *,
    route_id: str,
    matched_module: str,
    blocked_routes: list[str] | None = None,
    matched_target: str = "",
    trace_chain: list[str] | None = None,
) -> OperationalRouteDecision:
    reply, intent, meta = handled
    merged = {k: str(v) for k, v in meta.items()}
    blocked = list(blocked_routes or [])
    if route_id == "failed_service_preemption":
        blocked = sorted(set(blocked) | BLOCKED_WHEN_PRIORITY)
    merged["route_id"] = route_id
    merged["matched_module"] = matched_module
    if blocked:
        merged["blocked_routes"] = ",".join(blocked)
    if matched_target:
        merged["matched_target"] = matched_target
    chain = list(trace_chain or [route_id])
    merged["route_trace"] = " → ".join(chain)
    decision = OperationalRouteDecision(
        reply=reply,
        intent=intent,
        meta=merged,
        route_id=route_id,
        matched_module=matched_module,
        blocked_routes=blocked,
        matched_target=matched_target,
        trace_chain=chain,
    )
    _log.info("Route trace: %s", merged["route_trace"])
    return decision


def record_master_route_trace(*, session_id: str, decision: OperationalRouteDecision) -> None:
    from aethos_core.chat.route_trace import save_last_route_trace

    save_last_route_trace(session_id=session_id, meta=decision.meta, intent=decision.intent)


def _matched_target_from_meta(meta: dict[str, str]) -> str:
    project = str(meta.get("project") or "—")
    environment = str(meta.get("environment") or "—")
    service = str(meta.get("service") or "—")
    if service != "—":
        return f"{project} / {environment} / {service}"
    return ""


def master_router_has_priority_route(text: str, *, session_id: str = "default") -> bool:
    """True when master router owns the turn before readonly/browser/Vercel diagnostics."""
    from aethos_core.config import get_settings

    if getattr(get_settings(), "chat_single_loop_enabled", True):
        return False
    if _in_master_route.get():
        return False

    from aethos_core.world_model.world_model_followup_router import is_world_model_followup

    if is_world_model_followup(text, session_id=session_id):
        return True

    from aethos_core.failed_service_investigation.global_preemption import (
        classify_failed_service_intent,
        is_cognition_owned_failure_investigation,
        should_preempt_to_failed_service,
    )

    if should_preempt_to_failed_service(text, session_id=session_id):
        return True

    if is_cognition_owned_failure_investigation(text, session_id=session_id):
        return True

    from aethos_core.operational_planner.planner_router import compose_planned_operational_reply_without_failed_service

    if compose_planned_operational_reply_without_failed_service(text, session_id=session_id) is not None:
        return True

    from aethos_core.chat.route_trace import is_internal_diagnostics_query

    if is_internal_diagnostics_query(text):
        return True

    from aethos_core.operational_state.narrative import compose_narrative_continuity_reply

    if compose_narrative_continuity_reply(text, session_id=session_id) is not None:
        return True

    return False


def probe_operational_master_route(
    text: str,
    *,
    session_id: str = "default",
    stop_before: str | None = "readonly_provider_diagnostics",
) -> OperationalRouteDecision | None:
    """Probe routing without readonly/browser/continuity phases."""
    if _in_master_route.get():
        return None
    token = _in_master_route.set(True)
    try:
        return resolve_operational_master_route(
            text,
            session_id=session_id,
            stop_before=stop_before,
        )
    finally:
        _in_master_route.reset(token)


def resolve_operational_master_route(
    text: str,
    *,
    session_id: str = "default",
    channel: str = "chat",
    stop_before: str | None = None,
) -> OperationalRouteDecision | None:
    if _in_master_route.get() and stop_before is None:
        return None
    entered_here = not _in_master_route.get()
    token = None
    if entered_here:
        token = _in_master_route.set(True)

    try:
        return _resolve_operational_master_route_impl(
            text,
            session_id=session_id,
            channel=channel,
            stop_before=stop_before,
        )
    finally:
        if entered_here and token is not None:
            _in_master_route.reset(token)


def _resolve_operational_master_route_impl(
    text: str,
    *,
    session_id: str = "default",
    channel: str = "chat",
    stop_before: str | None = None,
) -> OperationalRouteDecision | None:
    from aethos_core.operational_cognition.cognition_graph import resolve_operational_cognition

    decision = resolve_operational_cognition(
        text,
        session_id=session_id,
        channel=channel,
        stop_before=stop_before,
    )
    if decision is not None:
        _log.info("Route trace: %s", decision.meta.get("route_trace", decision.route_id))
    return decision
