# SPDX-License-Identifier: Apache-2.0
"""FIX 326 — strategic planning intelligence chat router."""

from __future__ import annotations

from aethos_core.mission_control.strategic_planning_intelligence.strategic_planning_intelligence_contract import (
    AUTOMATIC_BUDGET_ALLOCATION_ENABLED_FIX_326,
    AUTOMATIC_PROJECT_CREATION_ENABLED_FIX_326,
    AUTOMATIC_RESOURCE_ASSIGNMENT_ENABLED_FIX_326,
    AUTOMATIC_STRATEGY_EXECUTION_ENABLED_FIX_326,
    MUTATION_PERFORMED_FIX_326,
    STRATEGIC_PLANNING_AUTHORITY_FIX_326,
    STRATEGIC_PLANNING_INTELLIGENCE_ROUTE_ID,
)
from aethos_core.mission_control.strategic_planning_intelligence.strategic_planning_intelligence_intent import (
    handle_strategic_planning_intelligence_intent,
    parse_strategic_planning_intelligence_intent,
)
from aethos_core.mission_control.strategic_planning_intelligence.strategic_planning_intelligence_renderer import (
    render_strategic_planning_intelligence,
)
from aethos_core.mission_control.strategic_planning_intelligence.strategic_planning_intelligence_service import (
    build_strategic_planning_intelligence,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": STRATEGIC_PLANNING_INTELLIGENCE_ROUTE_ID,
        "matched_module": (
            "mission_control.strategic_planning_intelligence.strategic_planning_intelligence_router"
        ),
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_326 is False else "true",
        "strategic_planning_authority": "false" if STRATEGIC_PLANNING_AUTHORITY_FIX_326 is False else "true",
        "automatic_strategy_execution_enabled": "false"
        if AUTOMATIC_STRATEGY_EXECUTION_ENABLED_FIX_326 is False
        else "true",
        "automatic_project_creation_enabled": "false"
        if AUTOMATIC_PROJECT_CREATION_ENABLED_FIX_326 is False
        else "true",
        "automatic_budget_allocation_enabled": "false"
        if AUTOMATIC_BUDGET_ALLOCATION_ENABLED_FIX_326 is False
        else "true",
        "automatic_resource_assignment_enabled": "false"
        if AUTOMATIC_RESOURCE_ASSIGNMENT_ENABLED_FIX_326 is False
        else "true",
        "mutation_scope": "strategic_planning_intelligence",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "strategic_planning_without_execution_authority",
        **extra,
    }


def route_strategic_planning_intelligence(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    intent = parse_strategic_planning_intelligence_intent(text)
    if intent is None:
        return None

    sid = (session_id or "default").strip()[:64] or "default"
    handled = handle_strategic_planning_intelligence_intent(intent, session_id=sid)

    if handled.get("action") == "record":
        record = handled.get("record") or {}
        body = (
            f"Recorded planning review note ({record.get('kind', 'note')}). "
            "AethOS generates planning options; humans choose plans."
        )
        return (
            body,
            "mission_control_strategic_planning_intelligence_record",
            _meta(sid, stage="record", record_kind=str(record.get("kind") or "")),
        )

    focus = str(handled.get("focus") or "strategic_planning_dashboard")
    result = build_strategic_planning_intelligence(session_id=sid)
    markdown = render_strategic_planning_intelligence(result.strategic_planning_intelligence, focus=focus)
    dashboard = result.strategic_planning_intelligence.get("sections", {}).get("strategic_planning_dashboard", [{}])[0]
    headline = (
        "Strategic planning intelligence — scenario and plan options only. "
        f"Scenarios **{dashboard.get('scenario_count', 0)}**, strongest plan "
        f"**{dashboard.get('strongest_plan', 'unknown')}**. "
        "No automatic strategy execution."
    )
    body = f"{headline}\n\n{markdown}"
    return (
        body,
        "mission_control_strategic_planning_intelligence",
        _meta(
            sid,
            stage="view",
            focus=focus,
            scenario_count=str(dashboard.get("scenario_count", 0)),
        ),
    )
