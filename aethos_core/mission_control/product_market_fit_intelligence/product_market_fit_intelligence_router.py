# SPDX-License-Identifier: Apache-2.0
"""FIX 322 — product-market fit intelligence chat router."""

from __future__ import annotations

from aethos_core.mission_control.product_market_fit_intelligence.product_market_fit_intelligence_contract import (
    AUTOMATIC_FEATURE_CREATION_ENABLED_FIX_322,
    AUTOMATIC_PRICING_CHANGES_ENABLED_FIX_322,
    AUTOMATIC_PRODUCT_STRATEGY_ENABLED_FIX_322,
    PMF_AUTHORITY_FIX_322,
    MUTATION_PERFORMED_FIX_322,
    PRODUCT_MARKET_FIT_INTELLIGENCE_ROUTE_ID,
)
from aethos_core.mission_control.product_market_fit_intelligence.product_market_fit_intelligence_intent import (
    handle_product_market_fit_intelligence_intent,
    parse_product_market_fit_intelligence_intent,
)
from aethos_core.mission_control.product_market_fit_intelligence.product_market_fit_intelligence_renderer import (
    render_product_market_fit_intelligence,
)
from aethos_core.mission_control.product_market_fit_intelligence.product_market_fit_intelligence_service import (
    build_product_market_fit_intelligence,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": PRODUCT_MARKET_FIT_INTELLIGENCE_ROUTE_ID,
        "matched_module": (
            "mission_control.product_market_fit_intelligence.product_market_fit_intelligence_router"
        ),
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_322 is False else "true",
        "pmf_authority": "false" if PMF_AUTHORITY_FIX_322 is False else "true",
        "automatic_product_strategy_enabled": "false"
        if AUTOMATIC_PRODUCT_STRATEGY_ENABLED_FIX_322 is False
        else "true",
        "automatic_feature_creation_enabled": "false"
        if AUTOMATIC_FEATURE_CREATION_ENABLED_FIX_322 is False
        else "true",
        "automatic_pricing_changes_enabled": "false"
        if AUTOMATIC_PRICING_CHANGES_ENABLED_FIX_322 is False
        else "true",
        "mutation_scope": "product_market_fit_intelligence",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "pmf_intelligence_without_product_strategy_authority",
        **extra,
    }


def route_product_market_fit_intelligence(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    intent = parse_product_market_fit_intelligence_intent(text)
    if intent is None:
        return None

    sid = (session_id or "default").strip()[:64] or "default"
    handled = handle_product_market_fit_intelligence_intent(intent, session_id=sid)

    if handled.get("action") == "record":
        record = handled.get("record") or {}
        body = (
            f"Recorded PMF review note ({record.get('kind', 'note')}). "
            "PMF intelligence evaluates evidence; humans decide strategy."
        )
        return (
            body,
            "mission_control_product_market_fit_intelligence_record",
            _meta(sid, stage="record", record_kind=str(record.get("kind") or "")),
        )

    focus = str(handled.get("focus") or "product_market_fit_dashboard")
    result = build_product_market_fit_intelligence(session_id=sid)
    markdown = render_product_market_fit_intelligence(result.product_market_fit_intelligence, focus=focus)
    dashboard = result.product_market_fit_intelligence.get("sections", {}).get("product_market_fit_dashboard", [{}])[0]
    headline = (
        "Product-market fit intelligence — tenant-scoped value evidence only. "
        f"PMF level **{dashboard.get('pmf_overall_level', 'UNKNOWN')}**. "
        "No automatic product strategy or pricing changes."
    )
    body = f"{headline}\n\n{markdown}"
    return (
        body,
        "mission_control_product_market_fit_intelligence",
        _meta(
            sid,
            stage="view",
            focus=focus,
            pmf_level=str(dashboard.get("pmf_overall_level") or ""),
        ),
    )
