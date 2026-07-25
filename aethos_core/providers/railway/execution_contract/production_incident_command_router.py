# SPDX-License-Identifier: Apache-2.0
"""FIX 123 — production incident command router."""

from __future__ import annotations

from aethos_core.providers.railway.execution_contract.execution_context import (
    resolve_execution_id_for_plan,
)
from aethos_core.providers.railway.execution_contract.production_incident_command import (
    acknowledge_incident_command,
    assign_incident_commander,
    attach_context_to_incident,
    build_incident_context_bundle,
    close_production_incident,
    is_production_incident_command_intent,
    load_incident_for_execution,
    open_production_incident,
    parse_incident_decision,
    record_incident_decision,
)
from aethos_core.providers.railway.execution_contract.production_incident_command_renderer import (
    render_commander_status,
    render_customer_update_draft,
    render_incident_briefing,
    render_incident_decisions,
    render_incident_operator_checklist,
    render_incident_summary,
    render_incident_timeline,
    render_rollback_recommendation,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": "railway_production_incident_command",
        "matched_module": "providers.railway.execution_contract.production_incident_command_router",
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "incident_command_stage": stage,
        **extra,
    }


def _require_incident(execution_id: str) -> tuple[dict | None, str | None]:
    incident = load_incident_for_execution(execution_id=execution_id)
    if incident:
        return incident, None
    return None, (
        "No open production incident for this execution. "
        "Use `open railway production incident` first."
    )


def route_railway_production_incident_command(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    raw = (text or "").strip()
    if not is_production_incident_command_intent(raw):
        return None

    from aethos_core.providers.railway.deployment_lifecycle.deployment_lifecycle_session_hydration import (
        ensure_railway_deployment_lifecycle_for_lane,
    )

    lane = ensure_railway_deployment_lifecycle_for_lane(
        session_id=session_id,
        user_text=raw,
        require_plan=True,
    )
    plan = lane.plan or {}
    execution_id = resolve_execution_id_for_plan(session_id=session_id, plan=plan) if plan else ""

    if not execution_id:
        body = (
            "No execution_id for production plan. Complete production shadow plan enrollment first, "
            "then open an incident."
        )
        return body, "railway_production_incident_command_blocked", _meta(session_id, stage="blocked")

    if "open" in raw.lower() and "incident" in raw.lower():
        result = open_production_incident(
            execution_id=execution_id,
            plan=plan,
            session_id=session_id,
        )
        body = render_incident_summary(result.incident)
        intent = (
            "railway_production_incident_opened"
            if result.ok
            else "railway_production_incident_command_blocked"
        )
        return body, intent, _meta(
            session_id,
            stage="open",
            incident_id=str(result.incident.get("incident_id") or ""),
        )

    if "close" in raw.lower() and "incident" in raw.lower():
        result = close_production_incident(execution_id=execution_id, session_id=session_id)
        body = render_incident_summary(result.incident) if result.incident else result.detail
        intent = (
            "railway_production_incident_closed"
            if result.ok
            else "railway_production_incident_command_blocked"
        )
        return body, intent, _meta(session_id, stage="close")

    if "assign" in raw.lower() and "commander" in raw.lower():
        result = assign_incident_commander(
            execution_id=execution_id,
            user_text=raw,
            session_id=session_id,
        )
        body = render_commander_status(result.incident) if result.incident else result.detail
        intent = (
            "railway_production_incident_commander_assigned"
            if result.ok
            else "railway_production_incident_command_blocked"
        )
        return body, intent, _meta(session_id, stage="commander_assign")

    if "acknowledge" in raw.lower() and "incident command" in raw.lower():
        result = acknowledge_incident_command(
            execution_id=execution_id,
            user_text=raw,
            session_id=session_id,
        )
        body = render_commander_status(result.incident) if result.incident else result.detail
        intent = (
            "railway_production_incident_command_ack"
            if result.ok
            else "railway_production_incident_command_blocked"
        )
        return body, intent, _meta(session_id, stage="command_ack")

    decision = parse_incident_decision(raw)
    if decision:
        result = record_incident_decision(
            execution_id=execution_id,
            decision=decision,
            user_text=raw,
            session_id=session_id,
        )
        body = render_incident_decisions(result.incident) if result.incident else result.detail
        intent = (
            "railway_production_incident_decision"
            if result.ok
            else "railway_production_incident_command_blocked"
        )
        return body, intent, _meta(session_id, stage="decision", decision=decision)

    incident, err = _require_incident(execution_id)
    if err:
        if "briefing" in raw.lower():
            result = open_production_incident(
                execution_id=execution_id,
                plan=plan,
                session_id=session_id,
            )
            if result.ok:
                incident = result.incident
            else:
                return err, "railway_production_incident_command_blocked", _meta(
                    session_id, stage="blocked"
                )
        else:
            return err, "railway_production_incident_command_blocked", _meta(session_id, stage="blocked")

    incident = attach_context_to_incident(incident, plan=plan)
    bundle = build_incident_context_bundle(execution_id=execution_id, plan=plan)

    if "timeline" in raw.lower():
        body = render_incident_timeline(incident)
        return body, "railway_production_incident_timeline", _meta(
            session_id,
            stage="timeline",
            incident_id=str(incident.get("incident_id") or ""),
        )

    if "briefing" in raw.lower():
        body = render_incident_briefing(incident, bundle=bundle)
        return body, "railway_production_incident_briefing", _meta(session_id, stage="briefing")

    if "checklist" in raw.lower():
        body = render_incident_operator_checklist(incident)
        return body, "railway_production_incident_checklist", _meta(session_id, stage="checklist")

    if "customer update" in raw.lower():
        body = render_customer_update_draft(incident, bundle=bundle)
        return body, "railway_production_incident_customer_draft", _meta(
            session_id, stage="customer_draft"
        )

    if "decisions" in raw.lower():
        body = render_incident_decisions(incident)
        return body, "railway_production_incident_decisions", _meta(session_id, stage="decisions")

    if "commander status" in raw.lower():
        body = render_commander_status(incident)
        return body, "railway_production_incident_commander_status", _meta(
            session_id, stage="commander_status"
        )

    if "rollback recommendation" in raw.lower():
        body = render_rollback_recommendation(incident, bundle=bundle)
        return body, "railway_production_incident_rollback_recommendation", _meta(
            session_id, stage="rollback_recommendation"
        )

    body = render_incident_summary(incident)
    return body, "railway_production_incident", _meta(
        session_id,
        stage="incident",
        incident_id=str(incident.get("incident_id") or ""),
    )
