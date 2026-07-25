# SPDX-License-Identifier: Apache-2.0
"""FIX 318 — product analytics chat router."""

from __future__ import annotations

from aethos_core.mission_control.product_analytics_foundation.product_analytics_foundation_contract import (
    ANALYTICS_AUTHORITY_FIX_318,
    AUTOMATIC_BEHAVIOR_MODIFICATION_ENABLED_FIX_318,
    AUTOMATIC_PLAN_MUTATION_ENABLED_FIX_318,
    AUTOMATIC_USER_TARGETING_ENABLED_FIX_318,
    MUTATION_PERFORMED_FIX_318,
    PRODUCT_ANALYTICS_FOUNDATION_ROUTE_ID,
)
from aethos_core.mission_control.product_analytics_foundation.product_analytics_foundation_intent import (
    handle_product_analytics_foundation_intent,
    parse_product_analytics_foundation_intent,
)
from aethos_core.mission_control.product_analytics_foundation.product_analytics_foundation_renderer import (
    render_product_analytics_foundation,
)
from aethos_core.mission_control.product_analytics_foundation.product_analytics_foundation_service import (
    build_product_analytics_foundation,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": PRODUCT_ANALYTICS_FOUNDATION_ROUTE_ID,
        "matched_module": (
            "mission_control.product_analytics_foundation.product_analytics_foundation_router"
        ),
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_318 is False else "true",
        "analytics_authority": "false" if ANALYTICS_AUTHORITY_FIX_318 is False else "true",
        "automatic_behavior_modification_enabled": "false"
        if AUTOMATIC_BEHAVIOR_MODIFICATION_ENABLED_FIX_318 is False
        else "true",
        "automatic_user_targeting_enabled": "false"
        if AUTOMATIC_USER_TARGETING_ENABLED_FIX_318 is False
        else "true",
        "automatic_plan_mutation_enabled": "false"
        if AUTOMATIC_PLAN_MUTATION_ENABLED_FIX_318 is False
        else "true",
        "mutation_scope": "product_analytics_foundation",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "product_analytics_without_surveillance",
        **extra,
    }


def route_product_analytics_foundation(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    intent = parse_product_analytics_foundation_intent(text)
    if intent is None:
        return None

    sid = (session_id or "default").strip()[:64] or "default"
    handled = handle_product_analytics_foundation_intent(intent, session_id=sid)

    if handled.get("action") == "record":
        record = handled.get("record") or {}
        body = (
            f"Recorded analytics review note ({record.get('kind', 'note')}). "
            "Analytics visibility ≠ user surveillance; no automatic behavior modification."
        )
        return (
            body,
            "mission_control_product_analytics_foundation_record",
            _meta(sid, stage="record", record_kind=str(record.get("kind") or "")),
        )

    focus = str(handled.get("focus") or "analytics_dashboard")
    result = build_product_analytics_foundation(session_id=sid)
    markdown = render_product_analytics_foundation(result.product_analytics_foundation, focus=focus)
    dashboard = result.product_analytics_foundation.get("sections", {}).get("analytics_dashboard", [{}])[0]
    headline = (
        "Product analytics foundation — tenant-scoped behavioral evidence only. "
        f"Onboarding completion **{dashboard.get('onboarding_completion_rate_percent', 0)}%**. "
        "No automatic behavior modification."
    )
    body = f"{headline}\n\n{markdown}"
    return (
        body,
        "mission_control_product_analytics_foundation",
        _meta(
            sid,
            stage="view",
            focus=focus,
            onboarding_completion=str(dashboard.get("onboarding_completion_rate_percent", 0)),
        ),
    )
