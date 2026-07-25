# SPDX-License-Identifier: Apache-2.0
"""FIX 177 — chat router for gate-routed lane entry handoff."""

from __future__ import annotations

from aethos_core.mission_control.gate_routed_lane_entry_handoff.gate_routed_lane_entry_handoff_contract import (
    AUTONOMOUS_EXECUTION_ENABLED_FIX_177,
    AUTONOMOUS_LANE_ENTRY_ENABLED_FIX_177,
    EXECUTION_PERFORMED_FIX_177,
    GATE_BYPASS_ENABLED_FIX_177,
    GATE_ROUTED_LANE_ENTRY_HANDOFF_ROUTE_ID,
    LANE_ADMISSION_EXECUTED_FIX_177,
    LANE_ENTRY_EXECUTION_PERFORMED_FIX_177,
    MUTATION_PERFORMED_FIX_177,
)
from aethos_core.mission_control.gate_routed_lane_entry_handoff.gate_routed_lane_entry_handoff_intent import (
    is_gate_routed_lane_entry_handoff_intent,
    parse_gate_routed_lane_entry_handoff_record_intent,
)
from aethos_core.mission_control.gate_routed_lane_entry_handoff.gate_routed_lane_entry_handoff_renderer import (
    render_gate_routed_lane_entry_handoff,
)
from aethos_core.mission_control.gate_routed_lane_entry_handoff.gate_routed_lane_entry_handoff_service import (
    build_gate_routed_lane_entry_handoff,
)
from aethos_core.mission_control.gate_routed_lane_entry_handoff.gate_routed_lane_entry_handoff_store import (
    append_gate_routed_lane_entry_handoff_record,
)
from aethos_core.mission_control.human_lane_admission_decision.human_lane_admission_decision_service import (
    build_human_lane_admission_decision,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": GATE_ROUTED_LANE_ENTRY_HANDOFF_ROUTE_ID,
        "matched_module": "mission_control.gate_routed_lane_entry_handoff.gate_routed_lane_entry_handoff_router",
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_177 is False else "true",
        "execution_performed": "false" if EXECUTION_PERFORMED_FIX_177 is False else "true",
        "lane_entry_execution_performed": "false" if LANE_ENTRY_EXECUTION_PERFORMED_FIX_177 is False else "true",
        "lane_admission_executed": "false" if LANE_ADMISSION_EXECUTED_FIX_177 is False else "true",
        "autonomous_execution_enabled": "false" if AUTONOMOUS_EXECUTION_ENABLED_FIX_177 is False else "true",
        "autonomous_lane_entry_enabled": "false" if AUTONOMOUS_LANE_ENTRY_ENABLED_FIX_177 is False else "true",
        "gate_bypass_enabled": "false" if GATE_BYPASS_ENABLED_FIX_177 is False else "true",
        "mutation_scope": "gate_routed_lane_entry_handoff_memory_only",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "gate_handoff_not_lane_entry_execution",
        **extra,
    }


def route_gate_routed_lane_entry_handoff(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    record_intent = parse_gate_routed_lane_entry_handoff_record_intent(text)
    if record_intent is not None:
        kind, content = record_intent
        decision = build_human_lane_admission_decision(session_id=session_id)
        ctx = decision.human_lane_admission_decision if decision.ok else {}
        record, blockers = append_gate_routed_lane_entry_handoff_record(
            session_id=session_id,
            kind=kind,
            content=content,
            plan_id=str(ctx.get("plan_id") or "") or None,
            correlation_id=str(ctx.get("correlation_id") or "") or None,
        )
        if blockers or not record:
            body = f"Gate-routed lane entry handoff record blocked: {', '.join(blockers)}"
            return (
                body,
                "mission_control_gate_routed_lane_entry_handoff_record_blocked",
                _meta(session_id, stage="blocked"),
            )
        body = (
            f"Gate handoff record persisted (`{record.get('record_id')}`, kind `{kind}`). "
            "Handoff only — frozen gate validates and decides lane entry."
        )
        return (
            body,
            "mission_control_gate_routed_lane_entry_handoff_record",
            _meta(
                session_id,
                stage="gate_routed_lane_entry_handoff_record",
                record_id=str(record.get("record_id") or ""),
                gate_routed_lane_entry_handoff_memory_only="true",
            ),
        )

    if not is_gate_routed_lane_entry_handoff_intent(text):
        return None

    result = build_gate_routed_lane_entry_handoff(session_id=session_id)
    if not result.ok:
        body = f"Gate-routed lane entry handoff unavailable: {', '.join(result.blockers)}"
        return (
            body,
            "mission_control_gate_routed_lane_entry_handoff_blocked",
            _meta(session_id, stage="blocked"),
        )

    body = render_gate_routed_lane_entry_handoff(result.gate_routed_lane_entry_handoff)
    return (
        body,
        "mission_control_gate_routed_lane_entry_handoff",
        _meta(
            session_id,
            stage="gate_routed_lane_entry_handoff",
            gate_handoff_record_count=str(
                result.gate_routed_lane_entry_handoff.get("gate_handoff_record_count", 0)
            ),
        ),
    )
