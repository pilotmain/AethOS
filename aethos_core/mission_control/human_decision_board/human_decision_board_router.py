# SPDX-License-Identifier: Apache-2.0
"""FIX 166 — chat router for human decision board."""

from __future__ import annotations

from aethos_core.mission_control.human_decision_board.human_decision_board_contract import (
    AUTONOMOUS_SELECTION_ENABLED_FIX_166,
    HUMAN_DECISION_BOARD_ROUTE_ID,
    MUTATION_PERFORMED_FIX_166,
)
from aethos_core.mission_control.human_decision_board.human_decision_board_intent import (
    is_human_decision_board_intent,
    parse_decision_record_intent,
)
from aethos_core.mission_control.human_decision_board.human_decision_board_renderer import (
    render_human_decision_board,
)
from aethos_core.mission_control.human_decision_board.human_decision_board_service import build_human_decision_board
from aethos_core.mission_control.human_decision_board.human_decision_board_store import (
    append_human_decision_board_record,
)
from aethos_core.mission_control.mission_planning_deliberation.mission_planning_deliberation_service import (
    build_mission_planning_deliberation,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": HUMAN_DECISION_BOARD_ROUTE_ID,
        "matched_module": "mission_control.human_decision_board.human_decision_board_router",
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_166 is False else "true",
        "autonomous_selection_enabled": "false" if AUTONOMOUS_SELECTION_ENABLED_FIX_166 is False else "true",
        "mutation_scope": "human_decision_board_memory_only",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "human_choice_not_system_selection",
        **extra,
    }


def route_human_decision_board(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    record_intent = parse_decision_record_intent(text)
    if record_intent is not None:
        kind, content = record_intent
        deliberation = build_mission_planning_deliberation(session_id=session_id)
        delib = deliberation.mission_planning_deliberation if deliberation.ok else {}
        record, blockers = append_human_decision_board_record(
            session_id=session_id,
            kind=kind,
            content=content,
            plan_id=str(delib.get("plan_id") or "") or None,
            correlation_id=str(delib.get("correlation_id") or "") or None,
        )
        if blockers or not record:
            body = f"Human decision board record blocked: {', '.join(blockers)}"
            return body, "mission_control_human_decision_board_record_blocked", _meta(session_id, stage="blocked")
        body = (
            f"Human decision board record persisted (`{record.get('record_id')}`, kind `{kind}`). "
            "Human choice only — no autonomous selection or execution authority."
        )
        return (
            body,
            "mission_control_human_decision_board_record",
            _meta(
                session_id,
                stage="human_decision_board_record",
                record_id=str(record.get("record_id") or ""),
                human_decision_board_memory_only="true",
            ),
        )

    if not is_human_decision_board_intent(text):
        return None

    result = build_human_decision_board(session_id=session_id)
    if not result.ok:
        body = f"Human decision board unavailable: {', '.join(result.blockers)}"
        return body, "mission_control_human_decision_board_blocked", _meta(session_id, stage="blocked")

    body = render_human_decision_board(result.human_decision_board)
    return (
        body,
        "mission_control_human_decision_board",
        _meta(
            session_id,
            stage="human_decision_board",
            decision_record_count=str(result.human_decision_board.get("decision_record_count", 0)),
        ),
    )
