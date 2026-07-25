# SPDX-License-Identifier: Apache-2.0
"""FIX 138 — chat router for governed rerun planning."""

from __future__ import annotations

from aethos_core.mission_control.rerun_planning.rerun_plan_contract import (
    MUTATION_PERFORMED_FIX_138,
    RERUN_EXECUTION_ENABLED_FIX_138,
    RERUN_PLAN_ROUTE_ID,
)
from aethos_core.mission_control.rerun_planning.rerun_plan_intent import is_governed_rerun_plan_intent
from aethos_core.mission_control.rerun_planning.rerun_plan_renderer import render_governed_rerun_plan
from aethos_core.mission_control.rerun_planning.rerun_plan_service import build_governed_rerun_plan


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": RERUN_PLAN_ROUTE_ID,
        "matched_module": "mission_control.rerun_planning.rerun_plan_router",
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_138 is False else "true",
        "rerun_execution_enabled": "false" if RERUN_EXECUTION_ENABLED_FIX_138 is False else "true",
        "mutation_scope": "rerun_planning_only",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "planning_not_execution",
        **extra,
    }


def route_governed_rerun_plan(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    if not is_governed_rerun_plan_intent(text):
        return None

    result = build_governed_rerun_plan(session_id=session_id)
    if not result.ok:
        body = f"Governed rerun plan unavailable: {', '.join(result.blockers)}"
        return body, "mission_control_rerun_plan_blocked", _meta(session_id, stage="blocked")

    plan = result.plan
    body = render_governed_rerun_plan(plan)
    return (
        body,
        "mission_control_rerun_plan",
        _meta(
            session_id,
            stage="rerun_plan",
            plan_id=str(plan.get("plan_id") or ""),
            correlation_id=str(plan.get("correlation_id") or ""),
            eligible=str(plan.get("eligibility", {}).get("eligible_for_planning", False)),
        ),
    )
