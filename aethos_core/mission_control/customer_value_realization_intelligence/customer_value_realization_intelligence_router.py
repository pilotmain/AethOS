# SPDX-License-Identifier: Apache-2.0
"""FIX 323 — customer value realization intelligence chat router."""

from __future__ import annotations

from aethos_core.mission_control.customer_value_realization_intelligence.customer_value_realization_intelligence_contract import (
    AUTOMATIC_CUSTOMER_OUTREACH_ENABLED_FIX_323,
    AUTOMATIC_CUSTOMER_SUCCESS_ENABLED_FIX_323,
    AUTOMATIC_GOAL_MODIFICATION_ENABLED_FIX_323,
    CUSTOMER_VALUE_REALIZATION_INTELLIGENCE_ROUTE_ID,
    MUTATION_PERFORMED_FIX_323,
    VALUE_REALIZATION_AUTHORITY_FIX_323,
)
from aethos_core.mission_control.customer_value_realization_intelligence.customer_value_realization_intelligence_intent import (
    handle_customer_value_realization_intelligence_intent,
    parse_customer_value_realization_intelligence_intent,
)
from aethos_core.mission_control.customer_value_realization_intelligence.customer_value_realization_intelligence_renderer import (
    render_customer_value_realization_intelligence,
)
from aethos_core.mission_control.customer_value_realization_intelligence.customer_value_realization_intelligence_service import (
    build_customer_value_realization_intelligence,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": CUSTOMER_VALUE_REALIZATION_INTELLIGENCE_ROUTE_ID,
        "matched_module": (
            "mission_control.customer_value_realization_intelligence.customer_value_realization_intelligence_router"
        ),
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_323 is False else "true",
        "value_realization_authority": "false" if VALUE_REALIZATION_AUTHORITY_FIX_323 is False else "true",
        "automatic_customer_success_enabled": "false"
        if AUTOMATIC_CUSTOMER_SUCCESS_ENABLED_FIX_323 is False
        else "true",
        "automatic_customer_outreach_enabled": "false"
        if AUTOMATIC_CUSTOMER_OUTREACH_ENABLED_FIX_323 is False
        else "true",
        "automatic_goal_modification_enabled": "false"
        if AUTOMATIC_GOAL_MODIFICATION_ENABLED_FIX_323 is False
        else "true",
        "mutation_scope": "customer_value_realization_intelligence",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "value_realization_without_customer_success_authority",
        **extra,
    }


def route_customer_value_realization_intelligence(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    intent = parse_customer_value_realization_intelligence_intent(text)
    if intent is None:
        return None

    sid = (session_id or "default").strip()[:64] or "default"
    handled = handle_customer_value_realization_intelligence_intent(intent, session_id=sid)

    if handled.get("action") == "record":
        record = handled.get("record") or {}
        body = (
            f"Recorded value review note ({record.get('kind', 'note')}). "
            "Value realization intelligence measures outcomes; humans decide customer strategy."
        )
        return (
            body,
            "mission_control_customer_value_realization_intelligence_record",
            _meta(sid, stage="record", record_kind=str(record.get("kind") or "")),
        )

    focus = str(handled.get("focus") or "customer_value_dashboard")
    result = build_customer_value_realization_intelligence(session_id=sid)
    markdown = render_customer_value_realization_intelligence(result.customer_value_realization_intelligence, focus=focus)
    dashboard = result.customer_value_realization_intelligence.get("sections", {}).get("customer_value_dashboard", [{}])[0]
    headline = (
        "Customer value realization intelligence — tenant-scoped outcome evidence only. "
        f"Level **{dashboard.get('value_realization_level', 'UNKNOWN')}**. "
        "No automatic customer success or outreach."
    )
    body = f"{headline}\n\n{markdown}"
    return (
        body,
        "mission_control_customer_value_realization_intelligence",
        _meta(
            sid,
            stage="view",
            focus=focus,
            value_level=str(dashboard.get("value_realization_level") or ""),
        ),
    )
