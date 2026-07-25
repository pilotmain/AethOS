# SPDX-License-Identifier: Apache-2.0
"""FIX 120 — production rollback escalation router."""

from __future__ import annotations

import re

from aethos_core.providers.railway.execution_contract.execution_context import (
    resolve_execution_id_for_plan,
)
from aethos_core.providers.railway.execution_contract.production_rollback_escalation import (
    acknowledge_incident_commander,
    assess_rollback_escalation_gate,
    create_or_refresh_escalation_from_verification,
    is_production_rollback_escalation_intent,
    parse_decision_state_from_text,
    record_human_rollback_decision,
    record_rollback_rehearsal_quorum_from_text,
)
from aethos_core.providers.railway.execution_contract.production_rollback_escalation_store import (
    load_escalation,
)
from aethos_core.providers.railway.execution_contract.production_rollback_escalation_renderer import (
    render_rollback_escalation_audit_trail,
    render_rollback_escalation_gate,
    render_rollback_escalation_ticket,
)

_ACK_RX = re.compile(
    r"\backnowledge\s+production\s+rollback\s+escalation\b",
    re.I,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": "railway_production_rollback_escalation",
        "matched_module": "providers.railway.execution_contract.production_rollback_escalation_router",
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "rollback_escalation_stage": stage,
        **extra,
    }


def route_railway_production_rollback_escalation(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    raw = (text or "").strip()
    if not is_production_rollback_escalation_intent(raw):
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

    if _ACK_RX.search(raw):
        if not execution_id:
            body = "No execution_id loaded. Complete production plan enrollment first."
            return body, "railway_production_rollback_escalation_blocked", _meta(
                session_id, stage="blocked"
            )
        record = acknowledge_incident_commander(
            execution_id=execution_id,
            user_text=raw,
            session_id=session_id,
        )
        body = render_rollback_escalation_ticket(record)
        return body, "railway_production_rollback_escalation_ack", _meta(
            session_id,
            stage="incident_commander_ack",
            decision_state=str(record.get("decision_state") or ""),
        )

    decision_state = parse_decision_state_from_text(raw)
    if decision_state:
        if not execution_id:
            body = "No execution_id loaded."
            return body, "railway_production_rollback_escalation_blocked", _meta(
                session_id, stage="blocked"
            )
        record = record_human_rollback_decision(
            execution_id=execution_id,
            decision_state=decision_state,
            user_text=raw,
            session_id=session_id,
        )
        body = render_rollback_escalation_ticket(record)
        return body, "railway_production_rollback_escalation_decision", _meta(
            session_id,
            stage="human_decision",
            decision_state=decision_state,
        )

    if "audit trail" in raw.lower():
        if not execution_id:
            body = "No escalation ticket for this execution."
            return body, "railway_production_rollback_escalation_blocked", _meta(
                session_id, stage="blocked"
            )
        record = load_escalation(execution_id=execution_id) or create_or_refresh_escalation_from_verification(
            execution_id=execution_id,
            plan=plan,
            session_id=session_id,
        )
        body = render_rollback_escalation_audit_trail(record)
        return body, "railway_production_rollback_escalation_audit", _meta(
            session_id,
            stage="audit_trail",
        )

    if "rehearsal quorum" in raw.lower():
        gate = assess_rollback_escalation_gate(
            execution_id=execution_id,
            plan=plan,
            user_text=raw,
            session_id=session_id,
        )
        if execution_id:
            record_rollback_rehearsal_quorum_from_text(
                execution_id=execution_id,
                user_text=raw,
                session_id=session_id,
            )
            gate = assess_rollback_escalation_gate(
                execution_id=execution_id,
                plan=plan,
                user_text=raw,
                session_id=session_id,
            )
        body = render_rollback_escalation_gate(gate)
        return body, "railway_production_rollback_rehearsal_quorum", _meta(
            session_id,
            stage="rehearsal_quorum",
            ready=str(gate.ready_for_shadow_rehearsal).lower(),
        )

    if not execution_id:
        body = "No execution_id for production plan."
        return body, "railway_production_rollback_escalation_blocked", _meta(session_id, stage="blocked")

    record = create_or_refresh_escalation_from_verification(
        execution_id=execution_id,
        plan=plan,
        session_id=session_id,
    )
    body = render_rollback_escalation_ticket(record)
    return body, "railway_production_rollback_escalation", _meta(
        session_id,
        stage="escalation_ticket",
        decision_state=str(record.get("decision_state") or ""),
    )
