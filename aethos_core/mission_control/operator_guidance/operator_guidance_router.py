# SPDX-License-Identifier: Apache-2.0
"""FIX 142 — chat router for operator contextual guidance."""

from __future__ import annotations

from aethos_core.mission_control.operator_guidance.operator_guidance_contract import (
    AUTOMATIC_MUTATION_PLANNING_ENABLED_FIX_142,
    AUTONOMOUS_EXECUTION_ENABLED_FIX_142,
    OPERATOR_GUIDANCE_ROUTE_ID,
    MUTATION_PERFORMED_FIX_142,
)
from aethos_core.mission_control.operator_guidance.operator_guidance_intent import is_operator_guidance_intent
from aethos_core.mission_control.operator_guidance.operator_guidance_renderer import render_operator_guidance
from aethos_core.mission_control.operator_guidance.operator_guidance_service import build_operator_contextual_guidance


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": OPERATOR_GUIDANCE_ROUTE_ID,
        "matched_module": "mission_control.operator_guidance.operator_guidance_router",
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_142 is False else "true",
        "autonomous_execution_enabled": "false" if AUTONOMOUS_EXECUTION_ENABLED_FIX_142 is False else "true",
        "automatic_mutation_planning_enabled": "false"
        if AUTOMATIC_MUTATION_PLANNING_ENABLED_FIX_142 is False
        else "true",
        "mutation_scope": "operator_guidance_only",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "copiloting_not_execution",
        **extra,
    }


def route_operator_guidance(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    if not is_operator_guidance_intent(text):
        return None

    result = build_operator_contextual_guidance(session_id=session_id)
    if not result.ok:
        body = f"Operator guidance unavailable: {', '.join(result.blockers)}"
        return body, "mission_control_operator_guidance_blocked", _meta(session_id, stage="blocked")

    body = render_operator_guidance(result.guidance)
    return (
        body,
        "mission_control_operator_guidance",
        _meta(
            session_id,
            stage="operator_guidance",
            recommendation_count=str(result.guidance.get("recommendation_count", 0)),
            plan_id=str(result.guidance.get("plan_id") or ""),
        ),
    )
