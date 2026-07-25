# SPDX-License-Identifier: Apache-2.0
"""FIX 146 — chat router for coordinated mission orchestration."""

from __future__ import annotations

from aethos_core.mission_control.mission_orchestration.mission_orchestration_contract import (
    AUTONOMOUS_ORCHESTRATION_ENABLED_FIX_146,
    MISSION_ORCHESTRATION_ROUTE_ID,
    MUTATION_PERFORMED_FIX_146,
)
from aethos_core.mission_control.mission_orchestration.mission_orchestration_intent import (
    is_mission_orchestration_intent,
)
from aethos_core.mission_control.mission_orchestration.mission_orchestration_renderer import (
    render_mission_orchestration,
)
from aethos_core.mission_control.mission_orchestration.mission_orchestration_service import (
    build_mission_orchestration,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": MISSION_ORCHESTRATION_ROUTE_ID,
        "matched_module": "mission_control.mission_orchestration.mission_orchestration_router",
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_146 is False else "true",
        "autonomous_orchestration_enabled": "false"
        if AUTONOMOUS_ORCHESTRATION_ENABLED_FIX_146 is False
        else "true",
        "mutation_scope": "mission_orchestration_only",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "orchestration_not_execution",
        **extra,
    }


def route_mission_orchestration(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    if not is_mission_orchestration_intent(text):
        return None

    result = build_mission_orchestration(session_id=session_id)
    if not result.ok:
        body = f"Mission orchestration unavailable: {', '.join(result.blockers)}"
        return body, "mission_control_mission_orchestration_blocked", _meta(session_id, stage="blocked")

    body = render_mission_orchestration(result.orchestration)
    readiness = (result.orchestration.get("sections") or {}).get("orchestration_readiness_scoring") or {}
    return (
        body,
        "mission_control_mission_orchestration",
        _meta(
            session_id,
            stage="mission_orchestration",
            recommendation_count=str(result.orchestration.get("recommendation_count", 0)),
            readiness_label=str(readiness.get("readiness_label", "")),
        ),
    )
