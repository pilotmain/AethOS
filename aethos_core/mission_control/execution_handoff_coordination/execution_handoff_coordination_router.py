# SPDX-License-Identifier: Apache-2.0
"""FIX 167 — chat router for execution handoff coordination."""

from __future__ import annotations

from aethos_core.mission_control.execution_handoff_coordination.execution_handoff_coordination_contract import (
    AUTONOMOUS_EXECUTION_ENABLED_FIX_167,
    AUTONOMOUS_LANE_ENTRY_ENABLED_FIX_167,
    EXECUTION_HANDOFF_COORDINATION_ROUTE_ID,
    MUTATION_PERFORMED_FIX_167,
)
from aethos_core.mission_control.execution_handoff_coordination.execution_handoff_coordination_intent import (
    is_execution_handoff_coordination_intent,
    parse_handoff_record_intent,
)
from aethos_core.mission_control.execution_handoff_coordination.execution_handoff_coordination_renderer import (
    render_execution_handoff_coordination,
)
from aethos_core.mission_control.execution_handoff_coordination.execution_handoff_coordination_service import (
    build_execution_handoff_coordination,
)
from aethos_core.mission_control.execution_handoff_coordination.execution_handoff_coordination_store import (
    append_execution_handoff_coordination_record,
)
from aethos_core.mission_control.human_decision_board.human_decision_board_service import build_human_decision_board


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": EXECUTION_HANDOFF_COORDINATION_ROUTE_ID,
        "matched_module": "mission_control.execution_handoff_coordination.execution_handoff_coordination_router",
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_167 is False else "true",
        "autonomous_execution_enabled": "false" if AUTONOMOUS_EXECUTION_ENABLED_FIX_167 is False else "true",
        "autonomous_lane_entry_enabled": "false"
        if AUTONOMOUS_LANE_ENTRY_ENABLED_FIX_167 is False
        else "true",
        "mutation_scope": "execution_handoff_coordination_memory_only",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "handoff_coordination_not_execution_authority",
        **extra,
    }


def route_execution_handoff_coordination(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    record_intent = parse_handoff_record_intent(text)
    if record_intent is not None:
        kind, content = record_intent
        decision = build_human_decision_board(session_id=session_id)
        board = decision.human_decision_board if decision.ok else {}
        record, blockers = append_execution_handoff_coordination_record(
            session_id=session_id,
            kind=kind,
            content=content,
            plan_id=str(board.get("plan_id") or "") or None,
            correlation_id=str(board.get("correlation_id") or "") or None,
        )
        if blockers or not record:
            body = f"Execution handoff record blocked: {', '.join(blockers)}"
            return (
                body,
                "mission_control_execution_handoff_coordination_record_blocked",
                _meta(session_id, stage="blocked"),
            )
        body = (
            f"Execution handoff record persisted (`{record.get('record_id')}`, kind `{kind}`). "
            "Handoff coordination only — no execution authority."
        )
        return (
            body,
            "mission_control_execution_handoff_coordination_record",
            _meta(
                session_id,
                stage="execution_handoff_coordination_record",
                record_id=str(record.get("record_id") or ""),
                execution_handoff_coordination_memory_only="true",
            ),
        )

    if not is_execution_handoff_coordination_intent(text):
        return None

    result = build_execution_handoff_coordination(session_id=session_id)
    if not result.ok:
        body = f"Execution handoff coordination unavailable: {', '.join(result.blockers)}"
        return body, "mission_control_execution_handoff_coordination_blocked", _meta(session_id, stage="blocked")

    body = render_execution_handoff_coordination(result.execution_handoff_coordination)
    return (
        body,
        "mission_control_execution_handoff_coordination",
        _meta(
            session_id,
            stage="execution_handoff_coordination",
            handoff_record_count=str(result.execution_handoff_coordination.get("handoff_record_count", 0)),
        ),
    )
