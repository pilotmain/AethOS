# SPDX-License-Identifier: Apache-2.0
"""FIX 164 — chat router for mission planning."""

from __future__ import annotations

from aethos_core.mission_control.constitutional_synthesis.constitutional_synthesis_service import (
    build_constitutional_synthesis,
)
from aethos_core.mission_control.mission_planning.mission_planning_contract import (
    AUTONOMOUS_ACTION_EXECUTION_ENABLED_FIX_164,
    AUTO_PATH_SELECTION_ENABLED_FIX_164,
    MISSION_PLANNING_ROUTE_ID,
    MUTATION_PERFORMED_FIX_164,
)
from aethos_core.mission_control.mission_planning.mission_planning_intent import (
    is_mission_planning_intent,
    parse_planning_record_intent,
)
from aethos_core.mission_control.mission_planning.mission_planning_renderer import render_mission_planning
from aethos_core.mission_control.mission_planning.mission_planning_service import build_mission_planning
from aethos_core.mission_control.mission_planning.mission_planning_store import append_mission_planning_record


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": MISSION_PLANNING_ROUTE_ID,
        "matched_module": "mission_control.mission_planning.mission_planning_router",
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_164 is False else "true",
        "autonomous_action_execution_enabled": "false"
        if AUTONOMOUS_ACTION_EXECUTION_ENABLED_FIX_164 is False
        else "true",
        "auto_path_selection_enabled": "false" if AUTO_PATH_SELECTION_ENABLED_FIX_164 is False else "true",
        "mutation_scope": "mission_planning_memory_only",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "planning_cognition_not_execution_authority",
        **extra,
    }


def route_mission_planning(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    record_intent = parse_planning_record_intent(text)
    if record_intent is not None:
        kind, content = record_intent
        synthesis = build_constitutional_synthesis(session_id=session_id)
        syn = synthesis.constitutional_synthesis if synthesis.ok else {}
        record, blockers = append_mission_planning_record(
            session_id=session_id,
            kind=kind,
            content=content,
            plan_id=str(syn.get("plan_id") or "") or None,
            correlation_id=str(syn.get("correlation_id") or "") or None,
        )
        if blockers or not record:
            body = f"Mission planning record blocked: {', '.join(blockers)}"
            return body, "mission_control_mission_planning_record_blocked", _meta(session_id, stage="blocked")
        body = (
            f"Mission planning record persisted (`{record.get('record_id')}`, kind `{kind}`). "
            "Recommendation-only — no execution authority or autonomous path selection."
        )
        return (
            body,
            "mission_control_mission_planning_record",
            _meta(
                session_id,
                stage="mission_planning_record",
                record_id=str(record.get("record_id") or ""),
                mission_planning_memory_only="true",
            ),
        )

    if not is_mission_planning_intent(text):
        return None

    result = build_mission_planning(session_id=session_id)
    if not result.ok:
        body = f"Mission planning unavailable: {', '.join(result.blockers)}"
        return body, "mission_control_mission_planning_blocked", _meta(session_id, stage="blocked")

    body = render_mission_planning(result.mission_planning)
    return (
        body,
        "mission_control_mission_planning",
        _meta(
            session_id,
            stage="mission_planning",
            planning_record_count=str(result.mission_planning.get("planning_record_count", 0)),
        ),
    )
