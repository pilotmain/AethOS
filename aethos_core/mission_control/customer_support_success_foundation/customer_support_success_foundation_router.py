# SPDX-License-Identifier: Apache-2.0
"""FIX 310 — chat router for customer support & success foundation."""

from __future__ import annotations

from aethos_core.mission_control.customer_support_success_foundation.customer_support_success_foundation_contract import (
    AUTOMATIC_CUSTOMER_CONTACT_ENABLED_FIX_310,
    AUTOMATIC_ESCALATION_ENABLED_FIX_310,
    AUTOMATIC_PLAN_UPGRADE_ENABLED_FIX_310,
    AUTOMATIC_SUPPORT_RESOLUTION_ENABLED_FIX_310,
    CUSTOMER_SUPPORT_AUTHORITY_FIX_310,
    CUSTOMER_SUPPORT_SUCCESS_FOUNDATION_ROUTE_ID,
    MUTATION_PERFORMED_FIX_310,
)
from aethos_core.mission_control.customer_support_success_foundation.customer_support_success_foundation_intent import (
    handle_customer_support_success_foundation_intent,
    parse_customer_support_success_foundation_intent,
)
from aethos_core.mission_control.customer_support_success_foundation.customer_support_success_foundation_renderer import (
    render_customer_support_success_foundation,
)
from aethos_core.mission_control.customer_support_success_foundation.customer_support_success_foundation_service import (
    build_customer_support_success_foundation,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": CUSTOMER_SUPPORT_SUCCESS_FOUNDATION_ROUTE_ID,
        "matched_module": (
            "mission_control.customer_support_success_foundation.customer_support_success_foundation_router"
        ),
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_310 is False else "true",
        "customer_support_authority": "false" if CUSTOMER_SUPPORT_AUTHORITY_FIX_310 is False else "true",
        "automatic_customer_contact_enabled": "false"
        if AUTOMATIC_CUSTOMER_CONTACT_ENABLED_FIX_310 is False
        else "true",
        "automatic_escalation_enabled": "false" if AUTOMATIC_ESCALATION_ENABLED_FIX_310 is False else "true",
        "automatic_support_resolution_enabled": "false"
        if AUTOMATIC_SUPPORT_RESOLUTION_ENABLED_FIX_310 is False
        else "true",
        "automatic_plan_upgrade_enabled": "false"
        if AUTOMATIC_PLAN_UPGRADE_ENABLED_FIX_310 is False
        else "true",
        "mutation_scope": "customer_support_success_foundation",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "support_visibility_not_support_authority",
        **extra,
    }


def route_customer_support_success_foundation(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    intent = parse_customer_support_success_foundation_intent(text)
    if intent is None:
        return None

    sid = (session_id or "default").strip()[:64] or "default"
    handled = handle_customer_support_success_foundation_intent(intent, session_id=sid)

    if handled.get("action") == "record":
        record = handled.get("record") or {}
        body = (
            f"Recorded support note ({record.get('kind', 'note')}). "
            "Customer support visibility ≠ customer support authority."
        )
        return (
            body,
            "mission_control_customer_support_success_foundation_record",
            _meta(sid, stage="record", record_kind=str(record.get("kind") or "")),
        )

    focus = str(handled.get("focus") or "customer_support_success_dashboard")
    result = build_customer_support_success_foundation(session_id=sid)
    markdown = render_customer_support_success_foundation(
        result.customer_support_success_foundation,
        focus=focus,
    )
    dashboard = (
        (result.customer_support_success_foundation.get("sections") or {})
        .get("customer_support_success_dashboard", [{}])[0]
    )
    headline = (
        f"Tracking **{dashboard.get('healthy_count', 0)}** healthy and "
        f"**{dashboard.get('at_risk_count', 0)}** at-risk customers. "
        "Support visibility only — humans remain responsible for support actions."
    )
    body = f"{headline}\n\n{markdown}"
    return (
        body,
        "mission_control_customer_support_success_foundation",
        _meta(
            sid,
            stage="view",
            focus=focus,
            at_risk_count=str(dashboard.get("at_risk_count") or 0),
        ),
    )
