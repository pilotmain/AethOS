# SPDX-License-Identifier: Apache-2.0
"""FIX 176 — chat router for human lane admission decision."""

from __future__ import annotations

from aethos_core.mission_control.governed_lane_readiness_board.governed_lane_readiness_board_service import (
    build_governed_lane_readiness_board,
)
from aethos_core.mission_control.human_lane_admission_decision.human_lane_admission_decision_contract import (
    AUTONOMOUS_EXECUTION_ENABLED_FIX_176,
    AUTONOMOUS_LANE_ENTRY_ENABLED_FIX_176,
    EXECUTION_PERFORMED_FIX_176,
    GATE_BYPASS_ENABLED_FIX_176,
    HUMAN_LANE_ADMISSION_DECISION_ROUTE_ID,
    LANE_ADMISSION_EXECUTED_FIX_176,
    LANE_ENTRY_EXECUTION_PERFORMED_FIX_176,
    MUTATION_PERFORMED_FIX_176,
)
from aethos_core.mission_control.human_lane_admission_decision.human_lane_admission_decision_intent import (
    is_human_lane_admission_decision_intent,
    parse_human_lane_admission_decision_record_intent,
)
from aethos_core.mission_control.human_lane_admission_decision.human_lane_admission_decision_renderer import (
    render_human_lane_admission_decision,
)
from aethos_core.mission_control.human_lane_admission_decision.human_lane_admission_decision_service import (
    build_human_lane_admission_decision,
)
from aethos_core.mission_control.human_lane_admission_decision.human_lane_admission_decision_store import (
    append_human_lane_admission_decision_record,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": HUMAN_LANE_ADMISSION_DECISION_ROUTE_ID,
        "matched_module": "mission_control.human_lane_admission_decision.human_lane_admission_decision_router",
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_176 is False else "true",
        "execution_performed": "false" if EXECUTION_PERFORMED_FIX_176 is False else "true",
        "lane_entry_execution_performed": "false" if LANE_ENTRY_EXECUTION_PERFORMED_FIX_176 is False else "true",
        "lane_admission_executed": "false" if LANE_ADMISSION_EXECUTED_FIX_176 is False else "true",
        "autonomous_execution_enabled": "false" if AUTONOMOUS_EXECUTION_ENABLED_FIX_176 is False else "true",
        "autonomous_lane_entry_enabled": "false" if AUTONOMOUS_LANE_ENTRY_ENABLED_FIX_176 is False else "true",
        "gate_bypass_enabled": "false" if GATE_BYPASS_ENABLED_FIX_176 is False else "true",
        "mutation_scope": "human_lane_admission_decision_memory_only",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "human_decision_not_lane_entry_execution",
        **extra,
    }


def route_human_lane_admission_decision(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    record_intent = parse_human_lane_admission_decision_record_intent(text)
    if record_intent is not None:
        kind, content = record_intent
        board = build_governed_lane_readiness_board(session_id=session_id)
        ctx = board.governed_lane_readiness_board if board.ok else {}
        record, blockers = append_human_lane_admission_decision_record(
            session_id=session_id,
            kind=kind,
            content=content,
            plan_id=str(ctx.get("plan_id") or "") or None,
            correlation_id=str(ctx.get("correlation_id") or "") or None,
        )
        if blockers or not record:
            body = f"Human lane admission decision record blocked: {', '.join(blockers)}"
            return (
                body,
                "mission_control_human_lane_admission_decision_record_blocked",
                _meta(session_id, stage="blocked"),
            )
        body = (
            f"Human lane admission decision record persisted (`{record.get('record_id')}`, kind `{kind}`). "
            "Decision recorded — lane entry execution not performed."
        )
        return (
            body,
            "mission_control_human_lane_admission_decision_record",
            _meta(
                session_id,
                stage="human_lane_admission_decision_record",
                record_id=str(record.get("record_id") or ""),
                human_lane_admission_decision_memory_only="true",
            ),
        )

    if not is_human_lane_admission_decision_intent(text):
        return None

    result = build_human_lane_admission_decision(session_id=session_id)
    if not result.ok:
        body = f"Human lane admission decision unavailable: {', '.join(result.blockers)}"
        return (
            body,
            "mission_control_human_lane_admission_decision_blocked",
            _meta(session_id, stage="blocked"),
        )

    body = render_human_lane_admission_decision(result.human_lane_admission_decision)
    return (
        body,
        "mission_control_human_lane_admission_decision",
        _meta(
            session_id,
            stage="human_lane_admission_decision",
            human_lane_admission_decision_record_count=str(
                result.human_lane_admission_decision.get("human_lane_admission_decision_record_count", 0)
            ),
        ),
    )
