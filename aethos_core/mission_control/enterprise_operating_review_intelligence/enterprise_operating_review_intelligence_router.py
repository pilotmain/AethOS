# SPDX-License-Identifier: Apache-2.0
"""FIX 329 — enterprise operating review intelligence chat router."""

from __future__ import annotations

from aethos_core.mission_control.enterprise_operating_review_intelligence.enterprise_operating_review_intelligence_contract import (
    AUTOMATIC_DECISION_EXECUTION_ENABLED_FIX_329,
    AUTOMATIC_ORGANIZATIONAL_CHANGES_ENABLED_FIX_329,
    AUTOMATIC_PROGRAM_EXECUTION_ENABLED_FIX_329,
    AUTOMATIC_STRATEGY_EXECUTION_ENABLED_FIX_329,
    ENTERPRISE_OPERATING_REVIEW_INTELLIGENCE_ROUTE_ID,
    MUTATION_PERFORMED_FIX_329,
    OPERATING_REVIEW_AUTHORITY_FIX_329,
)
from aethos_core.mission_control.enterprise_operating_review_intelligence.enterprise_operating_review_intelligence_intent import (
    handle_enterprise_operating_review_intelligence_intent,
    parse_enterprise_operating_review_intelligence_intent,
)
from aethos_core.mission_control.enterprise_operating_review_intelligence.enterprise_operating_review_intelligence_renderer import (
    render_enterprise_operating_review_intelligence,
)
from aethos_core.mission_control.enterprise_operating_review_intelligence.enterprise_operating_review_intelligence_service import (
    build_enterprise_operating_review_intelligence,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": ENTERPRISE_OPERATING_REVIEW_INTELLIGENCE_ROUTE_ID,
        "matched_module": (
            "mission_control.enterprise_operating_review_intelligence."
            "enterprise_operating_review_intelligence_router"
        ),
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_329 is False else "true",
        "operating_review_authority": "false" if OPERATING_REVIEW_AUTHORITY_FIX_329 is False else "true",
        "automatic_strategy_execution_enabled": "false"
        if AUTOMATIC_STRATEGY_EXECUTION_ENABLED_FIX_329 is False
        else "true",
        "automatic_program_execution_enabled": "false"
        if AUTOMATIC_PROGRAM_EXECUTION_ENABLED_FIX_329 is False
        else "true",
        "automatic_organizational_changes_enabled": "false"
        if AUTOMATIC_ORGANIZATIONAL_CHANGES_ENABLED_FIX_329 is False
        else "true",
        "automatic_decision_execution_enabled": "false"
        if AUTOMATIC_DECISION_EXECUTION_ENABLED_FIX_329 is False
        else "true",
        "mutation_scope": "enterprise_operating_review_intelligence",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "enterprise_operating_review_without_executive_authority",
        **extra,
    }


def route_enterprise_operating_review_intelligence(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    intent = parse_enterprise_operating_review_intelligence_intent(text)
    if intent is None:
        return None

    sid = (session_id or "default").strip()[:64] or "default"
    handled = handle_enterprise_operating_review_intelligence_intent(intent, session_id=sid)

    if handled.get("action") == "record":
        record = handled.get("record") or {}
        body = (
            f"Recorded operating review note ({record.get('kind', 'note')}). "
            "AethOS synthesizes evidence; humans make decisions."
        )
        return (
            body,
            "mission_control_enterprise_operating_review_intelligence_record",
            _meta(sid, stage="record", record_kind=str(record.get("kind") or "")),
        )

    focus = str(handled.get("focus") or "enterprise_operating_dashboard")
    result = build_enterprise_operating_review_intelligence(session_id=sid)
    markdown = render_enterprise_operating_review_intelligence(
        result.enterprise_operating_review_intelligence,
        focus=focus,
    )
    dashboard = result.enterprise_operating_review_intelligence.get("sections", {}).get(
        "enterprise_operating_dashboard",
        [{}],
    )[0]
    headline = (
        "Enterprise operating review intelligence — unified executive synthesis only. "
        f"Operating level **{dashboard.get('overall_operating_level', 'STABLE')}**, "
        f"major risks **{dashboard.get('major_risk_count', 0)}**. "
        "No automatic decision execution."
    )
    body = f"{headline}\n\n{markdown}"
    return (
        body,
        "mission_control_enterprise_operating_review_intelligence",
        _meta(
            sid,
            stage="view",
            focus=focus,
            operating_level=str(dashboard.get("overall_operating_level", "STABLE")),
        ),
    )
