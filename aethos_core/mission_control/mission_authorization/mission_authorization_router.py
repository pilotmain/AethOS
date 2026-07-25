# SPDX-License-Identifier: Apache-2.0
"""FIX 170 — chat router for mission authorization."""

from __future__ import annotations

from aethos_core.mission_control.human_decision_board.human_decision_board_service import build_human_decision_board
from aethos_core.mission_control.mission_authorization.mission_authorization_contract import (
    AUTONOMOUS_EXECUTION_ENABLED_FIX_170,
    GATE_BYPASS_ENABLED_FIX_170,
    MISSION_AUTHORIZATION_ROUTE_ID,
    MUTATION_PERFORMED_FIX_170,
)
from aethos_core.mission_control.mission_authorization.mission_authorization_intent import (
    is_mission_authorization_intent,
    parse_mission_authorization_record_intent,
)
from aethos_core.mission_control.mission_authorization.mission_authorization_renderer import (
    render_mission_authorization,
)
from aethos_core.mission_control.mission_authorization.mission_authorization_service import build_mission_authorization
from aethos_core.mission_control.mission_authorization.mission_authorization_store import append_mission_authorization_record


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": MISSION_AUTHORIZATION_ROUTE_ID,
        "matched_module": "mission_control.mission_authorization.mission_authorization_router",
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_170 is False else "true",
        "autonomous_execution_enabled": "false" if AUTONOMOUS_EXECUTION_ENABLED_FIX_170 is False else "true",
        "gate_bypass_enabled": "false" if GATE_BYPASS_ENABLED_FIX_170 is False else "true",
        "mutation_scope": "mission_authorization_memory_only",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "authorization_envelope_not_gate_bypass",
        **extra,
    }


def route_mission_authorization(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    record_intent = parse_mission_authorization_record_intent(text)
    if record_intent is not None:
        kind, content = record_intent
        decision = build_human_decision_board(session_id=session_id)
        board = decision.human_decision_board if decision.ok else {}
        record, blockers = append_mission_authorization_record(
            session_id=session_id,
            kind=kind,
            content=content,
            plan_id=str(board.get("plan_id") or "") or None,
            correlation_id=str(board.get("correlation_id") or "") or None,
        )
        if blockers or not record:
            body = f"Mission authorization record blocked: {', '.join(blockers)}"
            return body, "mission_control_mission_authorization_record_blocked", _meta(session_id, stage="blocked")
        body = (
            f"Mission authorization record persisted (`{record.get('record_id')}`, kind `{kind}`). "
            "Bounded envelope only — existing gates remain enforced."
        )
        return (
            body,
            "mission_control_mission_authorization_record",
            _meta(
                session_id,
                stage="mission_authorization_record",
                record_id=str(record.get("record_id") or ""),
                mission_authorization_memory_only="true",
            ),
        )

    if not is_mission_authorization_intent(text):
        return None

    result = build_mission_authorization(session_id=session_id)
    if not result.ok:
        body = f"Mission authorization unavailable: {', '.join(result.blockers)}"
        return body, "mission_control_mission_authorization_blocked", _meta(session_id, stage="blocked")

    body = render_mission_authorization(result.mission_authorization)
    return (
        body,
        "mission_control_mission_authorization",
        _meta(
            session_id,
            stage="mission_authorization",
            authorization_record_count=str(result.mission_authorization.get("authorization_record_count", 0)),
        ),
    )
