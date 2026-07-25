# SPDX-License-Identifier: Apache-2.0
"""FIX 324 — strategic portfolio intelligence chat router."""

from __future__ import annotations

from aethos_core.mission_control.strategic_portfolio_intelligence.strategic_portfolio_intelligence_contract import (
    AUTOMATIC_BUDGET_ALLOCATION_ENABLED_FIX_324,
    AUTOMATIC_PROJECT_CREATION_ENABLED_FIX_324,
    AUTOMATIC_RESOURCE_REALLOCATION_ENABLED_FIX_324,
    AUTOMATIC_STRATEGY_EXECUTION_ENABLED_FIX_324,
    MUTATION_PERFORMED_FIX_324,
    STRATEGIC_AUTHORITY_FIX_324,
    STRATEGIC_PORTFOLIO_INTELLIGENCE_ROUTE_ID,
)
from aethos_core.mission_control.strategic_portfolio_intelligence.strategic_portfolio_intelligence_intent import (
    handle_strategic_portfolio_intelligence_intent,
    parse_strategic_portfolio_intelligence_intent,
)
from aethos_core.mission_control.strategic_portfolio_intelligence.strategic_portfolio_intelligence_renderer import (
    render_strategic_portfolio_intelligence,
)
from aethos_core.mission_control.strategic_portfolio_intelligence.strategic_portfolio_intelligence_service import (
    build_strategic_portfolio_intelligence,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": STRATEGIC_PORTFOLIO_INTELLIGENCE_ROUTE_ID,
        "matched_module": (
            "mission_control.strategic_portfolio_intelligence.strategic_portfolio_intelligence_router"
        ),
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_324 is False else "true",
        "strategic_authority": "false" if STRATEGIC_AUTHORITY_FIX_324 is False else "true",
        "automatic_budget_allocation_enabled": "false"
        if AUTOMATIC_BUDGET_ALLOCATION_ENABLED_FIX_324 is False
        else "true",
        "automatic_project_creation_enabled": "false"
        if AUTOMATIC_PROJECT_CREATION_ENABLED_FIX_324 is False
        else "true",
        "automatic_resource_reallocation_enabled": "false"
        if AUTOMATIC_RESOURCE_REALLOCATION_ENABLED_FIX_324 is False
        else "true",
        "automatic_strategy_execution_enabled": "false"
        if AUTOMATIC_STRATEGY_EXECUTION_ENABLED_FIX_324 is False
        else "true",
        "mutation_scope": "strategic_portfolio_intelligence",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "strategic_portfolio_without_executive_authority",
        **extra,
    }


def route_strategic_portfolio_intelligence(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    intent = parse_strategic_portfolio_intelligence_intent(text)
    if intent is None:
        return None

    sid = (session_id or "default").strip()[:64] or "default"
    handled = handle_strategic_portfolio_intelligence_intent(intent, session_id=sid)

    if handled.get("action") == "record":
        record = handled.get("record") or {}
        body = (
            f"Recorded strategic review note ({record.get('kind', 'note')}). "
            "Portfolio intelligence evaluates evidence; humans make investment decisions."
        )
        return (
            body,
            "mission_control_strategic_portfolio_intelligence_record",
            _meta(sid, stage="record", record_kind=str(record.get("kind") or "")),
        )

    focus = str(handled.get("focus") or "strategic_portfolio_dashboard")
    result = build_strategic_portfolio_intelligence(session_id=sid)
    markdown = render_strategic_portfolio_intelligence(result.strategic_portfolio_intelligence, focus=focus)
    dashboard = result.strategic_portfolio_intelligence.get("sections", {}).get("strategic_portfolio_dashboard", [{}])[0]
    headline = (
        "Strategic portfolio intelligence — tenant-scoped portfolio evidence only. "
        f"Business value score **{dashboard.get('business_value_score', 0)}**. "
        "No automatic budget allocation or strategy execution."
    )
    body = f"{headline}\n\n{markdown}"
    return (
        body,
        "mission_control_strategic_portfolio_intelligence",
        _meta(
            sid,
            stage="view",
            focus=focus,
            business_value=str(dashboard.get("business_value_score", 0)),
        ),
    )
