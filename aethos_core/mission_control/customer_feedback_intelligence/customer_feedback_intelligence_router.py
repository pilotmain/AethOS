# SPDX-License-Identifier: Apache-2.0
"""FIX 319 — customer feedback intelligence chat router."""

from __future__ import annotations

from aethos_core.mission_control.customer_feedback_intelligence.customer_feedback_intelligence_contract import (
    AUTOMATIC_BACKLOG_CREATION_ENABLED_FIX_319,
    AUTOMATIC_CUSTOMER_CONTACT_ENABLED_FIX_319,
    AUTOMATIC_FEATURE_CREATION_ENABLED_FIX_319,
    CUSTOMER_FEEDBACK_INTELLIGENCE_ROUTE_ID,
    FEEDBACK_AUTHORITY_FIX_319,
    MUTATION_PERFORMED_FIX_319,
)
from aethos_core.mission_control.customer_feedback_intelligence.customer_feedback_intelligence_intent import (
    handle_customer_feedback_intelligence_intent,
    parse_customer_feedback_intelligence_intent,
)
from aethos_core.mission_control.customer_feedback_intelligence.customer_feedback_intelligence_renderer import (
    render_customer_feedback_intelligence,
)
from aethos_core.mission_control.customer_feedback_intelligence.customer_feedback_intelligence_service import (
    build_customer_feedback_intelligence,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": CUSTOMER_FEEDBACK_INTELLIGENCE_ROUTE_ID,
        "matched_module": (
            "mission_control.customer_feedback_intelligence.customer_feedback_intelligence_router"
        ),
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_319 is False else "true",
        "feedback_authority": "false" if FEEDBACK_AUTHORITY_FIX_319 is False else "true",
        "automatic_feature_creation_enabled": "false"
        if AUTOMATIC_FEATURE_CREATION_ENABLED_FIX_319 is False
        else "true",
        "automatic_backlog_creation_enabled": "false"
        if AUTOMATIC_BACKLOG_CREATION_ENABLED_FIX_319 is False
        else "true",
        "automatic_customer_contact_enabled": "false"
        if AUTOMATIC_CUSTOMER_CONTACT_ENABLED_FIX_319 is False
        else "true",
        "mutation_scope": "customer_feedback_intelligence",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "feedback_intelligence_without_customer_authority",
        **extra,
    }


def route_customer_feedback_intelligence(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    intent = parse_customer_feedback_intelligence_intent(text)
    if intent is None:
        return None

    sid = (session_id or "default").strip()[:64] or "default"
    handled = handle_customer_feedback_intelligence_intent(intent, session_id=sid)

    if handled.get("action") == "record":
        record = handled.get("record") or {}
        body = (
            f"Recorded feedback review note ({record.get('kind', 'note')}). "
            "Feedback informs decisions; no automatic work creation."
        )
        return (
            body,
            "mission_control_customer_feedback_intelligence_record",
            _meta(sid, stage="record", record_kind=str(record.get("kind") or "")),
        )

    focus = str(handled.get("focus") or "customer_feedback_dashboard")
    result = build_customer_feedback_intelligence(session_id=sid)
    markdown = render_customer_feedback_intelligence(result.customer_feedback_intelligence, focus=focus)
    dashboard = result.customer_feedback_intelligence.get("sections", {}).get("customer_feedback_dashboard", [{}])[0]
    headline = (
        "Customer feedback intelligence — tenant-scoped submitted feedback only. "
        f"**{dashboard.get('feedback_item_count', 0)}** feedback items tracked. "
        "No automatic backlog or customer contact."
    )
    body = f"{headline}\n\n{markdown}"
    return (
        body,
        "mission_control_customer_feedback_intelligence",
        _meta(
            sid,
            stage="view",
            focus=focus,
            feedback_item_count=str(dashboard.get("feedback_item_count", 0)),
        ),
    )
