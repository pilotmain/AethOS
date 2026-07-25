# SPDX-License-Identifier: Apache-2.0
"""FIX 165 — chat router for mission planning multi-agent deliberation."""

from __future__ import annotations

from aethos_core.mission_control.mission_planning.mission_planning_service import build_mission_planning
from aethos_core.mission_control.mission_planning_deliberation.mission_planning_deliberation_contract import (
    AUTONOMOUS_EXECUTION_ENABLED_FIX_165,
    AUTONOMOUS_LANE_SELECTION_ENABLED_FIX_165,
    MISSION_PLANNING_DELIBERATION_ROUTE_ID,
    MUTATION_PERFORMED_FIX_165,
)
from aethos_core.mission_control.mission_planning_deliberation.mission_planning_deliberation_intent import (
    is_mission_planning_deliberation_intent,
    parse_deliberation_record_intent,
)
from aethos_core.mission_control.mission_planning_deliberation.mission_planning_deliberation_renderer import (
    render_mission_planning_deliberation,
)
from aethos_core.mission_control.mission_planning_deliberation.mission_planning_deliberation_service import (
    build_mission_planning_deliberation,
)
from aethos_core.mission_control.mission_planning_deliberation.mission_planning_deliberation_store import (
    append_mission_planning_deliberation_record,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": MISSION_PLANNING_DELIBERATION_ROUTE_ID,
        "matched_module": "mission_control.mission_planning_deliberation.mission_planning_deliberation_router",
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_165 is False else "true",
        "autonomous_execution_enabled": "false" if AUTONOMOUS_EXECUTION_ENABLED_FIX_165 is False else "true",
        "autonomous_lane_selection_enabled": "false"
        if AUTONOMOUS_LANE_SELECTION_ENABLED_FIX_165 is False
        else "true",
        "mutation_scope": "mission_planning_deliberation_memory_only",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "deliberation_analysis_not_execution_authority",
        **extra,
    }


def route_mission_planning_deliberation(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    record_intent = parse_deliberation_record_intent(text)
    if record_intent is not None:
        kind, content = record_intent
        planning = build_mission_planning(session_id=session_id)
        mp = planning.mission_planning if planning.ok else {}
        record, blockers = append_mission_planning_deliberation_record(
            session_id=session_id,
            kind=kind,
            content=content,
            plan_id=str(mp.get("plan_id") or "") or None,
            correlation_id=str(mp.get("correlation_id") or "") or None,
        )
        if blockers or not record:
            body = f"Mission planning deliberation record blocked: {', '.join(blockers)}"
            return (
                body,
                "mission_control_mission_planning_deliberation_record_blocked",
                _meta(session_id, stage="blocked"),
            )
        body = (
            f"Mission planning deliberation record persisted (`{record.get('record_id')}`, kind `{kind}`). "
            "Analysis-only — no execution authority or autonomous path selection."
        )
        return (
            body,
            "mission_control_mission_planning_deliberation_record",
            _meta(
                session_id,
                stage="mission_planning_deliberation_record",
                record_id=str(record.get("record_id") or ""),
                mission_planning_deliberation_memory_only="true",
            ),
        )

    if not is_mission_planning_deliberation_intent(text):
        return None

    result = build_mission_planning_deliberation(session_id=session_id)
    if not result.ok:
        body = f"Mission planning deliberation unavailable: {', '.join(result.blockers)}"
        return body, "mission_control_mission_planning_deliberation_blocked", _meta(session_id, stage="blocked")

    body = render_mission_planning_deliberation(result.mission_planning_deliberation)
    return (
        body,
        "mission_control_mission_planning_deliberation",
        _meta(
            session_id,
            stage="mission_planning_deliberation",
            deliberation_record_count=str(result.mission_planning_deliberation.get("deliberation_record_count", 0)),
            agent_role_count=str(result.mission_planning_deliberation.get("agent_role_count", 0)),
        ),
    )
