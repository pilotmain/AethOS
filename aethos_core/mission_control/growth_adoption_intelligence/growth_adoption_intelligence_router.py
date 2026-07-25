# SPDX-License-Identifier: Apache-2.0
"""FIX 320 — growth & adoption intelligence chat router."""

from __future__ import annotations

from aethos_core.mission_control.growth_adoption_intelligence.growth_adoption_intelligence_contract import (
    AUTOMATIC_CUSTOMER_OUTREACH_ENABLED_FIX_320,
    AUTOMATIC_CUSTOMER_TARGETING_ENABLED_FIX_320,
    AUTOMATIC_GROWTH_EXECUTION_ENABLED_FIX_320,
    AUTOMATIC_PLAN_UPGRADE_ENABLED_FIX_320,
    GROWTH_ADOPTION_INTELLIGENCE_ROUTE_ID,
    GROWTH_AUTHORITY_FIX_320,
    MUTATION_PERFORMED_FIX_320,
)
from aethos_core.mission_control.growth_adoption_intelligence.growth_adoption_intelligence_intent import (
    handle_growth_adoption_intelligence_intent,
    parse_growth_adoption_intelligence_intent,
)
from aethos_core.mission_control.growth_adoption_intelligence.growth_adoption_intelligence_renderer import (
    render_growth_adoption_intelligence,
)
from aethos_core.mission_control.growth_adoption_intelligence.growth_adoption_intelligence_service import (
    build_growth_adoption_intelligence,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": GROWTH_ADOPTION_INTELLIGENCE_ROUTE_ID,
        "matched_module": (
            "mission_control.growth_adoption_intelligence.growth_adoption_intelligence_router"
        ),
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_320 is False else "true",
        "growth_authority": "false" if GROWTH_AUTHORITY_FIX_320 is False else "true",
        "automatic_customer_outreach_enabled": "false"
        if AUTOMATIC_CUSTOMER_OUTREACH_ENABLED_FIX_320 is False
        else "true",
        "automatic_plan_upgrade_enabled": "false"
        if AUTOMATIC_PLAN_UPGRADE_ENABLED_FIX_320 is False
        else "true",
        "automatic_customer_targeting_enabled": "false"
        if AUTOMATIC_CUSTOMER_TARGETING_ENABLED_FIX_320 is False
        else "true",
        "automatic_growth_execution_enabled": "false"
        if AUTOMATIC_GROWTH_EXECUTION_ENABLED_FIX_320 is False
        else "true",
        "mutation_scope": "growth_adoption_intelligence",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "growth_intelligence_without_growth_execution",
        **extra,
    }


def route_growth_adoption_intelligence(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    intent = parse_growth_adoption_intelligence_intent(text)
    if intent is None:
        return None

    sid = (session_id or "default").strip()[:64] or "default"
    handled = handle_growth_adoption_intelligence_intent(intent, session_id=sid)

    if handled.get("action") == "record":
        record = handled.get("record") or {}
        body = (
            f"Recorded growth review note ({record.get('kind', 'note')}). "
            "Growth intelligence identifies opportunities; humans decide actions."
        )
        return (
            body,
            "mission_control_growth_adoption_intelligence_record",
            _meta(sid, stage="record", record_kind=str(record.get("kind") or "")),
        )

    focus = str(handled.get("focus") or "growth_adoption_dashboard")
    result = build_growth_adoption_intelligence(session_id=sid)
    markdown = render_growth_adoption_intelligence(result.growth_adoption_intelligence, focus=focus)
    dashboard = result.growth_adoption_intelligence.get("sections", {}).get("growth_adoption_dashboard", [{}])[0]
    headline = (
        "Growth & adoption intelligence — tenant-scoped growth signals only. "
        f"**{dashboard.get('activated_customers', 0)}** activated customers; "
        f"adoption rate **{dashboard.get('adoption_rate_percent', 0)}%**. "
        "No automatic outreach or plan upgrades."
    )
    body = f"{headline}\n\n{markdown}"
    return (
        body,
        "mission_control_growth_adoption_intelligence",
        _meta(
            sid,
            stage="view",
            focus=focus,
            adoption_rate=str(dashboard.get("adoption_rate_percent", 0)),
        ),
    )
