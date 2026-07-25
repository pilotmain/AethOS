# SPDX-License-Identifier: Apache-2.0
"""FIX 327 — enterprise program intelligence chat router."""

from __future__ import annotations

from aethos_core.mission_control.enterprise_program_intelligence.enterprise_program_intelligence_contract import (
    AUTOMATIC_DEPENDENCY_RESOLUTION_ENABLED_FIX_327,
    AUTOMATIC_PROGRAM_EXECUTION_ENABLED_FIX_327,
    AUTOMATIC_PROJECT_CREATION_ENABLED_FIX_327,
    AUTOMATIC_RESOURCE_ASSIGNMENT_ENABLED_FIX_327,
    ENTERPRISE_PROGRAM_INTELLIGENCE_ROUTE_ID,
    MUTATION_PERFORMED_FIX_327,
    PROGRAM_AUTHORITY_FIX_327,
)
from aethos_core.mission_control.enterprise_program_intelligence.enterprise_program_intelligence_intent import (
    handle_enterprise_program_intelligence_intent,
    parse_enterprise_program_intelligence_intent,
)
from aethos_core.mission_control.enterprise_program_intelligence.enterprise_program_intelligence_renderer import (
    render_enterprise_program_intelligence,
)
from aethos_core.mission_control.enterprise_program_intelligence.enterprise_program_intelligence_service import (
    build_enterprise_program_intelligence,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": ENTERPRISE_PROGRAM_INTELLIGENCE_ROUTE_ID,
        "matched_module": (
            "mission_control.enterprise_program_intelligence.enterprise_program_intelligence_router"
        ),
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_327 is False else "true",
        "program_authority": "false" if PROGRAM_AUTHORITY_FIX_327 is False else "true",
        "automatic_project_creation_enabled": "false"
        if AUTOMATIC_PROJECT_CREATION_ENABLED_FIX_327 is False
        else "true",
        "automatic_program_execution_enabled": "false"
        if AUTOMATIC_PROGRAM_EXECUTION_ENABLED_FIX_327 is False
        else "true",
        "automatic_resource_assignment_enabled": "false"
        if AUTOMATIC_RESOURCE_ASSIGNMENT_ENABLED_FIX_327 is False
        else "true",
        "automatic_dependency_resolution_enabled": "false"
        if AUTOMATIC_DEPENDENCY_RESOLUTION_ENABLED_FIX_327 is False
        else "true",
        "mutation_scope": "enterprise_program_intelligence",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "enterprise_program_without_execution_authority",
        **extra,
    }


def route_enterprise_program_intelligence(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    intent = parse_enterprise_program_intelligence_intent(text)
    if intent is None:
        return None

    sid = (session_id or "default").strip()[:64] or "default"
    handled = handle_enterprise_program_intelligence_intent(intent, session_id=sid)

    if handled.get("action") == "record":
        record = handled.get("record") or {}
        body = (
            f"Recorded program review note ({record.get('kind', 'note')}). "
            "AethOS evaluates programs; humans execute programs."
        )
        return (
            body,
            "mission_control_enterprise_program_intelligence_record",
            _meta(sid, stage="record", record_kind=str(record.get("kind") or "")),
        )

    focus = str(handled.get("focus") or "enterprise_program_dashboard")
    result = build_enterprise_program_intelligence(session_id=sid)
    markdown = render_enterprise_program_intelligence(result.enterprise_program_intelligence, focus=focus)
    dashboard = result.enterprise_program_intelligence.get("sections", {}).get("enterprise_program_dashboard", [{}])[0]
    headline = (
        "Enterprise program intelligence — program evaluation only. "
        f"Programs **{dashboard.get('program_count', 0)}**, healthy "
        f"**{dashboard.get('healthy_program_count', 0)}**, blocked "
        f"**{dashboard.get('blocked_program_count', 0)}**. "
        "No automatic program execution."
    )
    body = f"{headline}\n\n{markdown}"
    return (
        body,
        "mission_control_enterprise_program_intelligence",
        _meta(
            sid,
            stage="view",
            focus=focus,
            program_count=str(dashboard.get("program_count", 0)),
        ),
    )
