# SPDX-License-Identifier: Apache-2.0
"""FIX 317 — chat router for continuous product improvement."""

from __future__ import annotations

from aethos_core.mission_control.continuous_product_improvement.continuous_product_improvement_contract import (
    AUTOMATIC_BACKLOG_CREATION_ENABLED_FIX_317,
    AUTOMATIC_FEATURE_CREATION_ENABLED_FIX_317,
    AUTOMATIC_PRODUCT_MUTATION_ENABLED_FIX_317,
    CONTINUOUS_IMPROVEMENT_AUTHORITY_FIX_317,
    CONTINUOUS_PRODUCT_IMPROVEMENT_ROUTE_ID,
    MUTATION_PERFORMED_FIX_317,
)
from aethos_core.mission_control.continuous_product_improvement.continuous_product_improvement_intent import (
    handle_continuous_product_improvement_intent,
    parse_continuous_product_improvement_intent,
)
from aethos_core.mission_control.continuous_product_improvement.continuous_product_improvement_renderer import (
    render_continuous_product_improvement,
)
from aethos_core.mission_control.continuous_product_improvement.continuous_product_improvement_service import (
    build_continuous_product_improvement,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": CONTINUOUS_PRODUCT_IMPROVEMENT_ROUTE_ID,
        "matched_module": (
            "mission_control.continuous_product_improvement.continuous_product_improvement_router"
        ),
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_317 is False else "true",
        "continuous_improvement_authority": "false"
        if CONTINUOUS_IMPROVEMENT_AUTHORITY_FIX_317 is False
        else "true",
        "automatic_backlog_creation_enabled": "false"
        if AUTOMATIC_BACKLOG_CREATION_ENABLED_FIX_317 is False
        else "true",
        "automatic_feature_creation_enabled": "false"
        if AUTOMATIC_FEATURE_CREATION_ENABLED_FIX_317 is False
        else "true",
        "automatic_product_mutation_enabled": "false"
        if AUTOMATIC_PRODUCT_MUTATION_ENABLED_FIX_317 is False
        else "true",
        "mutation_scope": "continuous_product_improvement",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "continuous_product_improvement_not_automatic_execution",
        **extra,
    }


def route_continuous_product_improvement(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    intent = parse_continuous_product_improvement_intent(text)
    if intent is None:
        return None

    sid = (session_id or "default").strip()[:64] or "default"
    handled = handle_continuous_product_improvement_intent(intent, session_id=sid)

    if handled.get("action") == "record":
        record = handled.get("record") or {}
        body = (
            f"Recorded improvement review note ({record.get('kind', 'note')}). "
            "Improvement recommendations ≠ automatic execution."
        )
        return (
            body,
            "mission_control_continuous_product_improvement_record",
            _meta(sid, stage="record", record_kind=str(record.get("kind") or "")),
        )

    focus = str(handled.get("focus") or "continuous_improvement_dashboard")
    result = build_continuous_product_improvement(session_id=sid)
    markdown = render_continuous_product_improvement(result.continuous_product_improvement, focus=focus)
    dashboard = result.continuous_product_improvement.get("sections", {}).get(
        "continuous_improvement_dashboard", [{}]
    )[0]
    opportunity_count = dashboard.get("opportunity_count", 0)
    headline = (
        f"Continuous product improvement — **{opportunity_count}** governed opportunities identified. "
        "Recommendations only; humans decide what to pursue."
    )
    body = f"{headline}\n\n{markdown}"
    return (
        body,
        "mission_control_continuous_product_improvement",
        _meta(
            sid,
            stage="view",
            focus=focus,
            opportunity_count=str(opportunity_count),
        ),
    )
