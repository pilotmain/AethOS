# SPDX-License-Identifier: Apache-2.0
"""FIX 321 — customer journey intelligence chat router."""

from __future__ import annotations

from aethos_core.mission_control.customer_journey_intelligence.customer_journey_intelligence_contract import (
    AUTOMATIC_CUSTOMER_INTERVENTION_ENABLED_FIX_321,
    AUTOMATIC_CUSTOMER_TARGETING_ENABLED_FIX_321,
    AUTOMATIC_JOURNEY_MODIFICATION_ENABLED_FIX_321,
    CUSTOMER_JOURNEY_INTELLIGENCE_ROUTE_ID,
    JOURNEY_AUTHORITY_FIX_321,
    MUTATION_PERFORMED_FIX_321,
)
from aethos_core.mission_control.customer_journey_intelligence.customer_journey_intelligence_intent import (
    handle_customer_journey_intelligence_intent,
    parse_customer_journey_intelligence_intent,
)
from aethos_core.mission_control.customer_journey_intelligence.customer_journey_intelligence_renderer import (
    render_customer_journey_intelligence,
)
from aethos_core.mission_control.customer_journey_intelligence.customer_journey_intelligence_service import (
    build_customer_journey_intelligence,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": CUSTOMER_JOURNEY_INTELLIGENCE_ROUTE_ID,
        "matched_module": (
            "mission_control.customer_journey_intelligence.customer_journey_intelligence_router"
        ),
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_321 is False else "true",
        "journey_authority": "false" if JOURNEY_AUTHORITY_FIX_321 is False else "true",
        "automatic_customer_targeting_enabled": "false"
        if AUTOMATIC_CUSTOMER_TARGETING_ENABLED_FIX_321 is False
        else "true",
        "automatic_customer_intervention_enabled": "false"
        if AUTOMATIC_CUSTOMER_INTERVENTION_ENABLED_FIX_321 is False
        else "true",
        "automatic_journey_modification_enabled": "false"
        if AUTOMATIC_JOURNEY_MODIFICATION_ENABLED_FIX_321 is False
        else "true",
        "mutation_scope": "customer_journey_intelligence",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "journey_intelligence_without_customer_manipulation",
        **extra,
    }


def route_customer_journey_intelligence(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    intent = parse_customer_journey_intelligence_intent(text)
    if intent is None:
        return None

    sid = (session_id or "default").strip()[:64] or "default"
    handled = handle_customer_journey_intelligence_intent(intent, session_id=sid)

    if handled.get("action") == "record":
        record = handled.get("record") or {}
        body = (
            f"Recorded journey review note ({record.get('kind', 'note')}). "
            "Journey intelligence observes paths; humans decide how to improve them."
        )
        return (
            body,
            "mission_control_customer_journey_intelligence_record",
            _meta(sid, stage="record", record_kind=str(record.get("kind") or "")),
        )

    focus = str(handled.get("focus") or "customer_journey_dashboard")
    result = build_customer_journey_intelligence(session_id=sid)
    markdown = render_customer_journey_intelligence(result.customer_journey_intelligence, focus=focus)
    dashboard = result.customer_journey_intelligence.get("sections", {}).get("customer_journey_dashboard", [{}])[0]
    headline = (
        "Customer journey intelligence — discovery through advocacy, tenant-scoped only. "
        f"Current stage **{dashboard.get('current_stage', '—')}**. "
        "No automatic customer intervention."
    )
    body = f"{headline}\n\n{markdown}"
    return (
        body,
        "mission_control_customer_journey_intelligence",
        _meta(
            sid,
            stage="view",
            focus=focus,
            current_stage=str(dashboard.get("current_stage") or ""),
        ),
    )
