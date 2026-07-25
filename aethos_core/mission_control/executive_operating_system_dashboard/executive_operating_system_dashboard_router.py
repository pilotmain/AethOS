# SPDX-License-Identifier: Apache-2.0
"""FIX 330 — executive operating system dashboard chat router."""

from __future__ import annotations

from aethos_core.mission_control.executive_operating_system_dashboard.executive_operating_system_dashboard_contract import (
    AUTOMATIC_DECISION_ENABLED_FIX_330,
    AUTOMATIC_EXECUTION_ENABLED_FIX_330,
    AUTOMATIC_OPERATIONAL_EXECUTION_ENABLED_FIX_330,
    AUTOMATIC_STRATEGY_EXECUTION_ENABLED_FIX_330,
    EXECUTIVE_DASHBOARD_AUTHORITY_FIX_330,
    EXECUTIVE_OPERATING_SYSTEM_DASHBOARD_ROUTE_ID,
    MUTATION_PERFORMED_FIX_330,
)
from aethos_core.mission_control.executive_operating_system_dashboard.executive_operating_system_dashboard_intent import (
    handle_executive_operating_system_dashboard_intent,
    parse_executive_operating_system_dashboard_intent,
)
from aethos_core.mission_control.executive_operating_system_dashboard.executive_operating_system_dashboard_renderer import (
    render_executive_operating_system_dashboard,
)
from aethos_core.mission_control.executive_operating_system_dashboard.executive_operating_system_dashboard_service import (
    build_executive_operating_system_dashboard_board,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": EXECUTIVE_OPERATING_SYSTEM_DASHBOARD_ROUTE_ID,
        "matched_module": (
            "mission_control.executive_operating_system_dashboard."
            "executive_operating_system_dashboard_router"
        ),
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_330 is False else "true",
        "executive_dashboard_authority": "false" if EXECUTIVE_DASHBOARD_AUTHORITY_FIX_330 is False else "true",
        "automatic_execution_enabled": "false" if AUTOMATIC_EXECUTION_ENABLED_FIX_330 is False else "true",
        "automatic_decision_enabled": "false" if AUTOMATIC_DECISION_ENABLED_FIX_330 is False else "true",
        "automatic_strategy_execution_enabled": "false"
        if AUTOMATIC_STRATEGY_EXECUTION_ENABLED_FIX_330 is False
        else "true",
        "automatic_operational_execution_enabled": "false"
        if AUTOMATIC_OPERATIONAL_EXECUTION_ENABLED_FIX_330 is False
        else "true",
        "mutation_scope": "executive_operating_system_dashboard",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "executive_dashboard_without_executive_authority",
        **extra,
    }


def route_executive_operating_system_dashboard(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    intent = parse_executive_operating_system_dashboard_intent(text)
    if intent is None:
        return None

    sid = (session_id or "default").strip()[:64] or "default"
    handled = handle_executive_operating_system_dashboard_intent(intent, session_id=sid)

    if handled.get("action") == "record":
        record = handled.get("record") or {}
        body = (
            f"Recorded dashboard note ({record.get('kind', 'note')}). "
            "The dashboard summarizes; humans decide."
        )
        return (
            body,
            "mission_control_executive_operating_system_dashboard_record",
            _meta(sid, stage="record", record_kind=str(record.get("kind") or "")),
        )

    focus = str(handled.get("focus") or "executive_operating_system_dashboard")
    result = build_executive_operating_system_dashboard_board(session_id=sid)
    markdown = render_executive_operating_system_dashboard(
        result.executive_operating_system_dashboard,
        focus=focus,
    )
    dashboard = result.executive_operating_system_dashboard.get("sections", {}).get(
        "executive_operating_system_dashboard",
        [{}],
    )[0]
    headline = (
        "Executive operating system dashboard — unified executive surface only. "
        f"Operating level **{dashboard.get('overall_operating_level', 'STABLE')}**, "
        f"attention items **{len(dashboard.get('executive_attention_items') or [])}**. "
        "No automatic execution."
    )
    body = f"{headline}\n\n{markdown}"
    return (
        body,
        "mission_control_executive_operating_system_dashboard",
        _meta(
            sid,
            stage="view",
            focus=focus,
            operating_level=str(dashboard.get("overall_operating_level", "STABLE")),
        ),
    )
