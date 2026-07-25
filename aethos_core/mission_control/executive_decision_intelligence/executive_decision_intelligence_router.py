# SPDX-License-Identifier: Apache-2.0
"""FIX 325 — executive decision intelligence chat router."""

from __future__ import annotations

from aethos_core.mission_control.executive_decision_intelligence.executive_decision_intelligence_contract import (
    AUTOMATIC_BUDGET_ALLOCATION_ENABLED_FIX_325,
    AUTOMATIC_DECISION_EXECUTION_ENABLED_FIX_325,
    AUTOMATIC_RESOURCE_REALLOCATION_ENABLED_FIX_325,
    AUTOMATIC_STRATEGY_EXECUTION_ENABLED_FIX_325,
    EXECUTIVE_DECISION_INTELLIGENCE_ROUTE_ID,
    MUTATION_PERFORMED_FIX_325,
    EXECUTIVE_AUTHORITY_FIX_325,
)
from aethos_core.mission_control.executive_decision_intelligence.executive_decision_intelligence_intent import (
    handle_executive_decision_intelligence_intent,
    parse_executive_decision_intelligence_intent,
)
from aethos_core.mission_control.executive_decision_intelligence.executive_decision_intelligence_renderer import (
    render_executive_decision_intelligence,
)
from aethos_core.mission_control.executive_decision_intelligence.executive_decision_intelligence_service import (
    build_executive_decision_intelligence,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": EXECUTIVE_DECISION_INTELLIGENCE_ROUTE_ID,
        "matched_module": (
            "mission_control.executive_decision_intelligence.executive_decision_intelligence_router"
        ),
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_325 is False else "true",
        "executive_authority": "false" if EXECUTIVE_AUTHORITY_FIX_325 is False else "true",
        "automatic_strategy_execution_enabled": "false"
        if AUTOMATIC_STRATEGY_EXECUTION_ENABLED_FIX_325 is False
        else "true",
        "automatic_resource_reallocation_enabled": "false"
        if AUTOMATIC_RESOURCE_REALLOCATION_ENABLED_FIX_325 is False
        else "true",
        "automatic_budget_allocation_enabled": "false"
        if AUTOMATIC_BUDGET_ALLOCATION_ENABLED_FIX_325 is False
        else "true",
        "automatic_decision_execution_enabled": "false"
        if AUTOMATIC_DECISION_EXECUTION_ENABLED_FIX_325 is False
        else "true",
        "mutation_scope": "executive_decision_intelligence",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "executive_decision_without_executive_authority",
        **extra,
    }


def route_executive_decision_intelligence(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    intent = parse_executive_decision_intelligence_intent(text)
    if intent is None:
        return None

    sid = (session_id or "default").strip()[:64] or "default"
    handled = handle_executive_decision_intelligence_intent(intent, session_id=sid)

    if handled.get("action") == "record":
        record = handled.get("record") or {}
        body = (
            f"Recorded executive review note ({record.get('kind', 'note')}). "
            "AethOS recommends; humans decide."
        )
        return (
            body,
            "mission_control_executive_decision_intelligence_record",
            _meta(sid, stage="record", record_kind=str(record.get("kind") or "")),
        )

    focus = str(handled.get("focus") or "executive_decision_dashboard")
    result = build_executive_decision_intelligence(session_id=sid)
    markdown = render_executive_decision_intelligence(result.executive_decision_intelligence, focus=focus)
    dashboard = result.executive_decision_intelligence.get("sections", {}).get("executive_decision_dashboard", [{}])[0]
    headline = (
        "Executive decision intelligence — evidence-backed recommendations only. "
        f"Pending decisions **{dashboard.get('pending_decision_count', 0)}**. "
        "No automatic decision execution."
    )
    body = f"{headline}\n\n{markdown}"
    return (
        body,
        "mission_control_executive_decision_intelligence",
        _meta(
            sid,
            stage="view",
            focus=focus,
            pending_decisions=str(dashboard.get("pending_decision_count", 0)),
        ),
    )
