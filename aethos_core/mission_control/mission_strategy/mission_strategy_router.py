# SPDX-License-Identifier: Apache-2.0
"""FIX 145 — chat router for mission strategy."""

from __future__ import annotations

from aethos_core.mission_control.mission_strategy.mission_strategy_contract import (
    AUTONOMOUS_PLANNING_ENABLED_FIX_145,
    MISSION_STRATEGY_ROUTE_ID,
    MUTATION_PERFORMED_FIX_145,
    ORGANIZATIONAL_SELF_DIRECTION_ENABLED_FIX_145,
)
from aethos_core.mission_control.mission_strategy.mission_strategy_intent import is_mission_strategy_intent
from aethos_core.mission_control.mission_strategy.mission_strategy_renderer import render_mission_strategy
from aethos_core.mission_control.mission_strategy.mission_strategy_service import build_mission_strategy


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": MISSION_STRATEGY_ROUTE_ID,
        "matched_module": "mission_control.mission_strategy.mission_strategy_router",
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_145 is False else "true",
        "autonomous_planning_enabled": "false" if AUTONOMOUS_PLANNING_ENABLED_FIX_145 is False else "true",
        "organizational_self_direction_enabled": "false"
        if ORGANIZATIONAL_SELF_DIRECTION_ENABLED_FIX_145 is False
        else "true",
        "mutation_scope": "mission_strategy_only",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "strategy_not_autonomy",
        **extra,
    }


def route_mission_strategy(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    if not is_mission_strategy_intent(text):
        return None

    result = build_mission_strategy(session_id=session_id)
    if not result.ok:
        body = f"Mission strategy unavailable: {', '.join(result.blockers)}"
        return body, "mission_control_mission_strategy_blocked", _meta(session_id, stage="blocked")

    body = render_mission_strategy(result.strategy)
    risk = (result.strategy.get("sections") or {}).get("organizational_risk_concentration") or {}
    return (
        body,
        "mission_control_mission_strategy",
        _meta(
            session_id,
            stage="mission_strategy",
            recommendation_count=str(result.strategy.get("recommendation_count", 0)),
            risk_label=str(risk.get("concentration_label", "")),
        ),
    )
