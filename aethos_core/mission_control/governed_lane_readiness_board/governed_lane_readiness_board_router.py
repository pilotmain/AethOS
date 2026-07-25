# SPDX-License-Identifier: Apache-2.0
"""FIX 175 — chat router for governed lane readiness board."""

from __future__ import annotations

from aethos_core.mission_control.governed_lane_entry_recommendation.governed_lane_entry_recommendation_service import (
    build_governed_lane_entry_recommendation,
)
from aethos_core.mission_control.governed_lane_readiness_board.governed_lane_readiness_board_contract import (
    AUTONOMOUS_EXECUTION_ENABLED_FIX_175,
    AUTONOMOUS_LANE_ENTRY_ENABLED_FIX_175,
    EXECUTION_PERFORMED_FIX_175,
    GATE_BYPASS_ENABLED_FIX_175,
    GOVERNED_LANE_READINESS_BOARD_ROUTE_ID,
    LANE_ADMISSION_DECISION_PERFORMED_FIX_175,
    MUTATION_PERFORMED_FIX_175,
)
from aethos_core.mission_control.governed_lane_readiness_board.governed_lane_readiness_board_intent import (
    is_governed_lane_readiness_board_intent,
    parse_governed_lane_readiness_board_record_intent,
)
from aethos_core.mission_control.governed_lane_readiness_board.governed_lane_readiness_board_renderer import (
    render_governed_lane_readiness_board,
)
from aethos_core.mission_control.governed_lane_readiness_board.governed_lane_readiness_board_service import (
    build_governed_lane_readiness_board,
)
from aethos_core.mission_control.governed_lane_readiness_board.governed_lane_readiness_board_store import (
    append_governed_lane_readiness_board_record,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": GOVERNED_LANE_READINESS_BOARD_ROUTE_ID,
        "matched_module": "mission_control.governed_lane_readiness_board.governed_lane_readiness_board_router",
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_175 is False else "true",
        "execution_performed": "false" if EXECUTION_PERFORMED_FIX_175 is False else "true",
        "lane_admission_decision_performed": "false" if LANE_ADMISSION_DECISION_PERFORMED_FIX_175 is False else "true",
        "autonomous_execution_enabled": "false" if AUTONOMOUS_EXECUTION_ENABLED_FIX_175 is False else "true",
        "autonomous_lane_entry_enabled": "false" if AUTONOMOUS_LANE_ENTRY_ENABLED_FIX_175 is False else "true",
        "gate_bypass_enabled": "false" if GATE_BYPASS_ENABLED_FIX_175 is False else "true",
        "mutation_scope": "governed_lane_readiness_board_memory_only",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "lane_readiness_board_not_admission_decision",
        **extra,
    }


def route_governed_lane_readiness_board(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    record_intent = parse_governed_lane_readiness_board_record_intent(text)
    if record_intent is not None:
        kind, content = record_intent
        recommendation = build_governed_lane_entry_recommendation(session_id=session_id)
        board = recommendation.governed_lane_entry_recommendation if recommendation.ok else {}
        record, blockers = append_governed_lane_readiness_board_record(
            session_id=session_id,
            kind=kind,
            content=content,
            plan_id=str(board.get("plan_id") or "") or None,
            correlation_id=str(board.get("correlation_id") or "") or None,
        )
        if blockers or not record:
            body = f"Governed lane readiness board record blocked: {', '.join(blockers)}"
            return (
                body,
                "mission_control_governed_lane_readiness_board_record_blocked",
                _meta(session_id, stage="blocked"),
            )
        body = (
            f"Lane readiness board record persisted (`{record.get('record_id')}`, kind `{kind}`). "
            "Board only — human decides lane admission in FIX 176."
        )
        return (
            body,
            "mission_control_governed_lane_readiness_board_record",
            _meta(
                session_id,
                stage="governed_lane_readiness_board_record",
                record_id=str(record.get("record_id") or ""),
                governed_lane_readiness_board_memory_only="true",
            ),
        )

    if not is_governed_lane_readiness_board_intent(text):
        return None

    result = build_governed_lane_readiness_board(session_id=session_id)
    if not result.ok:
        body = f"Governed lane readiness board unavailable: {', '.join(result.blockers)}"
        return (
            body,
            "mission_control_governed_lane_readiness_board_blocked",
            _meta(session_id, stage="blocked"),
        )

    body = render_governed_lane_readiness_board(result.governed_lane_readiness_board)
    return (
        body,
        "mission_control_governed_lane_readiness_board",
        _meta(
            session_id,
            stage="governed_lane_readiness_board",
            lane_readiness_board_record_count=str(
                result.governed_lane_readiness_board.get("lane_readiness_board_record_count", 0)
            ),
        ),
    )
