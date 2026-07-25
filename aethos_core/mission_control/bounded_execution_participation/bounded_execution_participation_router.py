# SPDX-License-Identifier: Apache-2.0
"""FIX 171 — chat router for bounded execution participation."""

from __future__ import annotations

from aethos_core.mission_control.bounded_execution_participation.bounded_execution_participation_contract import (
    AUTONOMOUS_EXECUTION_ENABLED_FIX_171,
    AUTONOMOUS_LANE_ENTRY_ENABLED_FIX_171,
    BOUNDED_EXECUTION_PARTICIPATION_ROUTE_ID,
    GATE_BYPASS_ENABLED_FIX_171,
    MUTATION_PERFORMED_FIX_171,
)
from aethos_core.mission_control.bounded_execution_participation.bounded_execution_participation_intent import (
    is_bounded_execution_participation_intent,
    parse_bounded_execution_participation_record_intent,
)
from aethos_core.mission_control.bounded_execution_participation.bounded_execution_participation_renderer import (
    render_bounded_execution_participation,
)
from aethos_core.mission_control.bounded_execution_participation.bounded_execution_participation_service import (
    build_bounded_execution_participation,
)
from aethos_core.mission_control.bounded_execution_participation.bounded_execution_participation_store import (
    append_bounded_execution_participation_record,
)
from aethos_core.mission_control.mission_authorization.mission_authorization_service import build_mission_authorization


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": BOUNDED_EXECUTION_PARTICIPATION_ROUTE_ID,
        "matched_module": "mission_control.bounded_execution_participation.bounded_execution_participation_router",
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_171 is False else "true",
        "autonomous_execution_enabled": "false" if AUTONOMOUS_EXECUTION_ENABLED_FIX_171 is False else "true",
        "autonomous_lane_entry_enabled": "false" if AUTONOMOUS_LANE_ENTRY_ENABLED_FIX_171 is False else "true",
        "gate_bypass_enabled": "false" if GATE_BYPASS_ENABLED_FIX_171 is False else "true",
        "mutation_scope": "bounded_execution_participation_memory_only",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "participation_coordination_not_lane_entry",
        **extra,
    }


def route_bounded_execution_participation(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    record_intent = parse_bounded_execution_participation_record_intent(text)
    if record_intent is not None:
        kind, content = record_intent
        auth = build_mission_authorization(session_id=session_id)
        board = auth.mission_authorization if auth.ok else {}
        record, blockers = append_bounded_execution_participation_record(
            session_id=session_id,
            kind=kind,
            content=content,
            plan_id=str(board.get("plan_id") or "") or None,
            correlation_id=str(board.get("correlation_id") or "") or None,
        )
        if blockers or not record:
            body = f"Bounded execution participation record blocked: {', '.join(blockers)}"
            return (
                body,
                "mission_control_bounded_execution_participation_record_blocked",
                _meta(session_id, stage="blocked"),
            )
        body = (
            f"Bounded execution participation record persisted (`{record.get('record_id')}`, kind `{kind}`). "
            "Envelope-scoped coordination only — existing gates remain enforced."
        )
        return (
            body,
            "mission_control_bounded_execution_participation_record",
            _meta(
                session_id,
                stage="bounded_execution_participation_record",
                record_id=str(record.get("record_id") or ""),
                bounded_execution_participation_memory_only="true",
            ),
        )

    if not is_bounded_execution_participation_intent(text):
        return None

    result = build_bounded_execution_participation(session_id=session_id)
    if not result.ok:
        body = f"Bounded execution participation unavailable: {', '.join(result.blockers)}"
        return (
            body,
            "mission_control_bounded_execution_participation_blocked",
            _meta(session_id, stage="blocked"),
        )

    body = render_bounded_execution_participation(result.bounded_execution_participation)
    return (
        body,
        "mission_control_bounded_execution_participation",
        _meta(
            session_id,
            stage="bounded_execution_participation",
            participation_record_count=str(result.bounded_execution_participation.get("participation_record_count", 0)),
        ),
    )
