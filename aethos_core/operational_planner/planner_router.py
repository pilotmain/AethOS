# SPDX-License-Identifier: Apache-2.0
"""Route planned operational queries before active-thread memory."""

from __future__ import annotations

from aethos_core.operational_planner.query_planner import OperationalQueryPlan, plan_operational_query


def should_override_active_thread(text: str, *, session_id: str = "default") -> bool:
    plan = plan_operational_query(text, session_id=session_id)
    return plan.overrides_active_thread


def compose_planned_operational_reply_without_failed_service(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    from aethos_core.response_composition.response_composer import try_compose_rerender_reply

    rerender = try_compose_rerender_reply(text, session_id=session_id)
    if rerender is not None:
        return rerender

    plan = plan_operational_query(text, session_id=session_id)

    if plan.action_type == "defer":
        return None
    if plan.action_type == "active_followup":
        return None
    if plan.action_type == "mutation":
        return None
    if plan.action_type == "clarify":
        body = (
            "That looks like a **provider-wide mutation**, which needs explicit per-service approval.\n\n"
            "Tell me which service to change, or ask for a provider-wide **health/inventory report** instead."
        )
        return body, "provider_wide_mutation_clarification", {"scope": plan.scope}

    if plan.action_type in {"provider_wide_readonly", "provider_readonly"}:
        return _compose_provider_wide_readonly(plan, session_id=session_id)

    return None


def compose_planned_operational_reply(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    planned = compose_planned_operational_reply_without_failed_service(text, session_id=session_id)
    if planned is not None:
        return planned

    from aethos_core.failed_service_investigation.global_preemption import route_failed_service_intent

    investigation = route_failed_service_intent(text, session_id=session_id)
    if investigation is not None:
        return investigation

    return None


def _compose_provider_wide_readonly(
    plan: OperationalQueryPlan,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    provider = plan.provider or "railway"
    active_service = ""

    from aethos_core.conversation.provider_memory.provider_followup_runtime import get_active_operational_thread

    thread = get_active_operational_thread(session_id)
    if thread is not None:
        active_service = str(getattr(thread, "service", "") or "")

    if provider == "railway" and plan.intent in {"inventory_health_report", "inventory_list"}:
        from aethos_core.operational_planner.adapters.railway_wide_health import compose_railway_provider_wide_health_reply

        return compose_railway_provider_wide_health_reply(
            user_text=plan.user_text,
            active_service=active_service,
            session_id=session_id,
        )

    from aethos_core.operational_planner.adapters.railway_wide_health import compose_provider_wide_stub_reply

    return compose_provider_wide_stub_reply(provider=provider, intent=plan.intent)
