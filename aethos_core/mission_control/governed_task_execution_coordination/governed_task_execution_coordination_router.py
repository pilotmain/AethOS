# SPDX-License-Identifier: Apache-2.0
"""FIX 172 — chat router for governed task execution coordination."""

from __future__ import annotations

from aethos_core.mission_control.bounded_execution_participation.bounded_execution_participation_service import (
    build_bounded_execution_participation,
)
from aethos_core.mission_control.governed_task_execution_coordination.governed_task_execution_coordination_contract import (
    AUTONOMOUS_EXECUTION_ENABLED_FIX_172,
    AUTONOMOUS_LANE_ENTRY_ENABLED_FIX_172,
    EXECUTION_PERFORMED_FIX_172,
    GATE_BYPASS_ENABLED_FIX_172,
    GOVERNED_TASK_EXECUTION_COORDINATION_ROUTE_ID,
    MUTATION_PERFORMED_FIX_172,
)
from aethos_core.mission_control.governed_task_execution_coordination.governed_task_execution_coordination_intent import (
    is_governed_task_execution_coordination_intent,
    parse_governed_task_execution_coordination_record_intent,
)
from aethos_core.mission_control.governed_task_execution_coordination.governed_task_execution_coordination_renderer import (
    render_governed_task_execution_coordination,
)
from aethos_core.mission_control.governed_task_execution_coordination.governed_task_execution_coordination_service import (
    build_governed_task_execution_coordination,
)
from aethos_core.mission_control.governed_task_execution_coordination.governed_task_execution_coordination_store import (
    append_governed_task_execution_coordination_record,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": GOVERNED_TASK_EXECUTION_COORDINATION_ROUTE_ID,
        "matched_module": "mission_control.governed_task_execution_coordination.governed_task_execution_coordination_router",
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_172 is False else "true",
        "execution_performed": "false" if EXECUTION_PERFORMED_FIX_172 is False else "true",
        "autonomous_execution_enabled": "false" if AUTONOMOUS_EXECUTION_ENABLED_FIX_172 is False else "true",
        "autonomous_lane_entry_enabled": "false" if AUTONOMOUS_LANE_ENTRY_ENABLED_FIX_172 is False else "true",
        "gate_bypass_enabled": "false" if GATE_BYPASS_ENABLED_FIX_172 is False else "true",
        "mutation_scope": "governed_task_execution_coordination_memory_only",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "execution_coordination_not_execution_authority",
        **extra,
    }


def route_governed_task_execution_coordination(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    record_intent = parse_governed_task_execution_coordination_record_intent(text)
    if record_intent is not None:
        kind, content = record_intent
        participation = build_bounded_execution_participation(session_id=session_id)
        board = participation.bounded_execution_participation if participation.ok else {}
        record, blockers = append_governed_task_execution_coordination_record(
            session_id=session_id,
            kind=kind,
            content=content,
            plan_id=str(board.get("plan_id") or "") or None,
            correlation_id=str(board.get("correlation_id") or "") or None,
        )
        if blockers or not record:
            body = f"Governed task execution coordination record blocked: {', '.join(blockers)}"
            return (
                body,
                "mission_control_governed_task_execution_coordination_record_blocked",
                _meta(session_id, stage="blocked"),
            )
        body = (
            f"Governed task execution coordination record persisted (`{record.get('record_id')}`, kind `{kind}`). "
            "Coordination only — existing gates remain enforced."
        )
        return (
            body,
            "mission_control_governed_task_execution_coordination_record",
            _meta(
                session_id,
                stage="governed_task_execution_coordination_record",
                record_id=str(record.get("record_id") or ""),
                governed_task_execution_coordination_memory_only="true",
            ),
        )

    if not is_governed_task_execution_coordination_intent(text):
        return None

    result = build_governed_task_execution_coordination(session_id=session_id)
    if not result.ok:
        body = f"Governed task execution coordination unavailable: {', '.join(result.blockers)}"
        return (
            body,
            "mission_control_governed_task_execution_coordination_blocked",
            _meta(session_id, stage="blocked"),
        )

    body = render_governed_task_execution_coordination(result.governed_task_execution_coordination)
    return (
        body,
        "mission_control_governed_task_execution_coordination",
        _meta(
            session_id,
            stage="governed_task_execution_coordination",
            coordination_record_count=str(
                result.governed_task_execution_coordination.get("coordination_record_count", 0)
            ),
        ),
    )
